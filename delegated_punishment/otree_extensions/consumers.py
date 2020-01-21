from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import datetime
from random import random
import numpy as np

from delegated_punishment.models import Player, Group, OfficerToken, Constants, GameData


def date_now_milli(): # todo: move this to another file
    return (datetime.datetime.now() - Constants.epoch).total_seconds() * 1000.0

class GameConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = 'group'
        self.room_name = 'room'

    def connect(self):

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # print("DISCONNECTING")
        # async_to_sync(self.channel_layer.group_discard)(
        #     self.room_group_name,
        #     self.channel_name
        # )
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        print_padding = 25

        data_json = json.loads(text_data) # todo: rename this text_data
        print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id'] #todo make this player_id_in_group?
        player = Player.objects.get(pk=player_id)
        group = Group.objects.get(pk=group_id) # can we delete this object? is it more efficient to search my pk rather than django object
        game_data = {}  # this is the json data that will be saved for this game event in database

        if data_json.get('balance'):
            current_balance = player.get_balance()
            current_roi = player.roi #this is here for debugging

            # Send message to WebSocket
            self.send(text_data=json.dumps({
                'balance': current_balance,
                'roi': current_roi #todo: remove
            }))

        elif data_json.get('harvest'):
            harvest_status = data_json['harvest']['status']
            player.harvest_status = harvest_status

            if player.harvest_status == 4:
                # increase balance
                player.balance = player.balance + Constants.civilian_income
                player.harvest_status = 0
            elif player.harvest_status == -1: #the player toggled screen losing progress on current harvest cycle
                # reset harvest status
                player.harvest_status = 0

            # print("PLAYER {} UPDATED HARVEST STATUS TO {}".format(player.pk, player.harvest_status))
            # print("PLAYER BALANCE: {}".format(player.balance))
            player.save()

            # EVENT
            thisdict = {
                "harvest_status": player.harvest_status,
                "player_balance": player.balance,
                "updated_at": date_now_milli(),
            }
            GameData.objects.create(p=player.id, g=group.id, jdata=thisdict)

            #todo do not need to send data down since there is no meaning. keep for debugging
            self.send(text_data=json.dumps({
                'harvest': player.balance,
                'status': player.harvest_status,
            }))

        elif data_json.get('defend_token_drag'):
            #save player location as 0 and send back confirmation
            print('TOKEN BEING DRAGGED')
            dtoken = data_json['defend_token_drag']
            token_num = dtoken['number']
            try:
                token = OfficerToken.objects.get(group=group, number=token_num)  # todo this will error if there are more than one result
            except OfficerToken.DoesNotExist:
                token = None
                print('ERROR: NO TOKEN WAS FOUND')

            # check if token was removed from investigations
            investigation_change = False
            if token.property == 11:
                investigation_change = True

            # set token to no property while it is being dragged
            token.property = 0
            token.x = 0
            token.y = 0
            token.save()

            # EVENT
            # thisdict = {
            #     "token_num": token_num,
            #     "token_property": token.property, # we do not need x and y
            #     "updated_at": date_now_milli(),
            # }
            # GameData.objects.create(p=player.id, g=group.id, jdata=thisdict)

            print('TOKEN WAS DRAGGED AND PROP SET TO ' + str(token.property))

            # update users with investigation token count
            if investigation_change:
                token_count = len(OfficerToken.objects.filter(group=group, property=11))  # make this null
                print('TOTAL TOKEN COUNT ' + str(token_count))

                # send token count to group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'investigation_update',
                        'investigation_count': token_count,
                    }
                )
            # EVENT we didnt add token total here because it can be calculated

        elif data_json.get('location_token_drag'):
            print('LOCATION TOKEN WAS DRAGGED')
            #get token and save it's location as 0
            dlocation = data_json['location_token_drag']

            # EVENT
            # thisdict = {
            #     "location": 0,
            #     "updated_at": date_now_milli(),
            # }

            # if player as in property before dragging update roi for stealing player and victim of the theft.
            if player.property > 0:
                # update victim roi
                victim = Player.objects.get(group=group, id_in_group=player.property)
                print('PLAYER WAS STEALING FROM PLAYER ' + str(victim.pk))
                victim.increase_roi()
                victim.last_updated = date_now_milli()
                victim.save()

                #EVENT
                # thisdict['victim'] = victim.id_in_group
                # thisdict['victim_roi'] = victim.roi
                # thisdict['victim_balance'] = victim.balance

                # update player roi
                player.decrease_roi()
                player.last_updated = date_now_milli()

                # EVENT
                # thisdict['player_roi'] = player.roi
                # thisdict['player_balance'] = player.balance
            else:
                print('PLAYER WAS NOT STEALING BEFORE')

            player.x = dlocation['x']
            player.y = dlocation['y']
            player.property = dlocation['property']
            player.save()

            #EVENT2
            # GameData.objects.create(p=player.id, g=group.id, jdata=thisdict)

            print('LOCATION DRAG TRANSCATION COMPLETE AND PROPERTY SET TO ' + str(player.property))

        elif data_json.get('investigation'):

            # set location to prop to 11 for investigation
            i_token = data_json['investigation']
            token_num = i_token['number']

            try:
                token = OfficerToken.objects.get(group=group, number=token_num)  # todo this will error if there are more than one result
            except OfficerToken.DoesNotExist:
                token = None

            if token.property == 11:
                # do nothing since token was already in investigation
                # send token count to group
                print('THIS TOKEN IS ALREADY IN INVESTIGATIONS')
            else:
                token.x = -1
                token.y = -1
                token.property = 11
                token.save()
                # get investigation token count
                token_count = len(OfficerToken.objects.filter(group=group, property=11)) #make this null
                print('TOTAL TOKEN COUNT ' + str(token_count))

                # EVENT
                # thisdict = {
                #     "token_count": token_count,
                #     "token_property": 11,  # 11 = investigation
                #     "updated_at": date_now_milli(),
                # }
                # GameData.objects.create(p=player.id, g=group.id, jdata=thisdict)

                #send token count to group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'investigation_update',
                        'investigation_count': token_count,
                    }
                )

        else: # these channel requests require more computation and send data down to all players

            intersections = []
            debug = []

            # EVENT DATA FOR THE FOLLOWING UPDATE TYPES
            # thisdict = {}

            if data_json.get('token'):
                token_update = data_json['token']
                token_num = token_update['number']

                # thisdict["token_num"] = token_num
                # thisdict["updated_at"] = date_now_milli() #todo change where updated_at is set

                try:
                    token = OfficerToken.objects.get(group=group, number=token_num) # todo this will error if there are more than one result
                except OfficerToken.DoesNotExist:
                    token = None
                    print('ERROR: NO TOKEN WAS FOUND')
                    # todo: research how we should exit here to prevent executing any more code

                token.property = token_update['property'] # todo: can't we do token_update.property?
                token.x = token_update['x']
                token.y = token_update['y']
                token.save()

                #EVENT2
                # thisdict['token_x'] = token.x
                # thisdict['token_y'] = token.y

                players_in_prop = Player.objects.filter(group=group, property=token.property)

                print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(print_padding), token_num, token.property, token.x, token.y))
                print("THERE ARE {} PLAYERS IN PROPERTY {}".format(len(players_in_prop), token.property))

                if players_in_prop:
                    for p in players_in_prop:
                        # intersections = Dict
                        print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('PLAYER'.ljust(print_padding), p.pk, p.property, p.x, p.y))
                        if token.x <= p.x <= (token.x + Constants.officer_token_size) and token.y <= p.y <= (token.y + Constants.officer_token_size):

                            print('{} {} AND PLAYER {}'.format('INTERSECTION BETWEEN TOKEN'.ljust(print_padding), token.number, p.pk))

                            # create intersection data
                            data = {'player': p.pk, 'y': p.y, 'x': p.x, 'property': p.property, 'token': token.number}
                            intersections.append(data)

                            # todo: update criminal and victim players roi here
                            # decrease robber roi
                            p.decrease_roi()
                            p.last_updated = date_now_milli()

                            # update victim roi
                            victim = Player.objects.get(group=group, id_in_group=p.property) # property here represents the player id in group since they line up in every group/game
                            victim.increase_roi()
                            victim.last_updated = date_now_milli()
                            victim.save()
                            # update victim

                            # update player info
                            p.property = 0
                            p.x = -1 # todo consider making this none and fixing logging issue
                            p.y = -1
                            p.last_updated = date_now_milli()
                            p.save()
                            print("PLAYER {} UPDATED AT {:6.2f}".format(p.pk, p.last_updated))

            elif data_json.get('steal'):

                steal_location = data_json['steal']
                player.x = steal_location['x']
                player.y = steal_location['y'] #todo: add this later so we only save once, not here then again after intersection
                player.property = steal_location['property']

                #EVENT2
                # thisdict["player_x"] = player.x
                # thisdict["player_y"] = player.y
                # thisdict["updated_at"] = date_now_milli()

                #todo: THIS IS PREVENTED ON THE FRONT END NOW.
                # is_in_own_property = player.property == player.id_in_group

                print("{} -- {} -- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('CIVILIAN LOCATION UPDATE'.ljust(print_padding), player.pk, player.property, player.x, player.y))

                # check for intersections
                tokens = OfficerToken.objects.filter(group=group, property=player.property)
                print('THERE ARE ' + str(len(tokens)) + ' TOKENS IN THIS PROPERTY')
                print("THERE ARE {} TOKENS IN PROPERTY {}".format(len(tokens), player.property))

                if tokens:
                    for token in tokens:
                        print("{} -- {}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(print_padding), token.number, token.property, token.x, token.y))
                        if token.x <= player.x <= (token.x + Constants.officer_token_size) and token.y <= player.y <= (token.y + Constants.officer_token_size):
                            print('\t\tINTERSECTION')

                            # create intersection data
                            data = {'player': player.pk, 'y': player.y, 'x': player.x, 'property': player.property, 'token': token.number}
                            intersections.append(data)

                            # update player info
                            player.property = 0
                            player.x = 0 # todo: probably change this back to None and make sure it doesn't break the logging
                            player.y = 0

                            break
                            # player.save() # This is preventing civilians from getting caught twice

                # if there was no intersection we update the roi of player and victim
                if player.property != 0:
                    # update player roi
                    player.increase_roi()

                    #EVENT3
                    # thisdict["player_roi"] = player.roi
                    # thisdict["player_balance"] = player.balance

                    # get victim object and update roi
                    victim = Player.objects.get(group=group, id_in_group=player.property)
                    victim.decrease_roi()
                    victim.last_updated = date_now_milli()
                    victim.save()

                    #EVENT4
                    # thisdict["victim_roi"] = victim.roi
                    # thisdict["player_balance"] = victim.balance

                player.last_updated = date_now_milli()
                print("PLAYER {} UPDATED AT {:6.2f}".format(player.pk, player.last_updated))
                player.save()

                # EVENT update save below

            num_investigators = len(OfficerToken.objects.filter(group=group, property=11))
            print('INVESTIGATION TOKEN COUNT: ' + str(num_investigators))
            if num_investigators > 0:
                for inter in intersections:
                    # MULTINULI PUNISH?
                    # print(inter)

                    # interdebug wezza
                    interdebug = {}

                    print('\t\tSTARTING NUMPY CALCULATIONS')
                    guilty = inter['player'] # int
                    innocent = inter['property'] # int
                    # police = 0
                    innocent_prob = 1 / 3 - num_investigators / 30
                    guilty_prob = 1 / 3 + 2 * num_investigators / 30
                    multi = [0, innocent_prob, innocent_prob, innocent_prob, innocent_prob]

                    # subtract 1 for 0 based index
                    multi[guilty - 1] = guilty_prob
                    multi[innocent - 1] = 0
                    print('\t\tMULTI' + str(multi))

                    #EVENT
                    # thisdict["multi"] = str(multi)
                    # wezza
                    interdebug['multi'] = str(multi)

                    result = np.random.multinomial(1, multi, 1)[0] # todo: document this syntax

                    convicted_player = -1
                    # determine which player was convicted from result
                    for i in range(len(result)):  # search array for result ex; [0,1,0,0,0]
                        if result[i] == 1:
                            convicted_pid = int(i + 1)
                            break
                    print('\t\tHERE IS THE NUMPY RESULT ' + str(result))

                    # EVENT
                    # thisdict["multi_result"] = str(result)
                    # wezza
                    interdebug['multi_result'] = str(result)

                    # updated convicted plater balance
                    print('CONVICTED PLAYER: ' + str(convicted_pid))
                    convicted_player = Player.objects.get(group=group, id_in_group=convicted_pid)
                    convicted_player.balance -= Constants.civilian_conviction_amount
                    convicted_player.save()

                    # EVENT
                    # thisdict["convicted_result"] = str(result)

                    # check if guilty player was convicted
                    wrongful_conviction = True
                    if convicted_pid == guilty:
                        print('THE CORRECT PLAYER WAS CONVICTED')
                        wrongful_conviction = False
                    else:
                        print('THE WRONG PLAYER WAS CONVICTED')

                    # UPDATE OFFICER BALANCE
                    officer = Player.objects.get(group=group, id_in_group=1) #todo we can check if the player is already the officer to prevent hitting db again
                    officer.balance += Constants.officer_intersection_payout

                    audit = np.random.binomial(1, Constants.officer_review_probability)
                    print('HERE IS THE AUDIT RESULT: ' + str(audit))
                    # wezza
                    interdebug['audit_result'] = str(audit)
                    interdebug['wrongful_conviction'] = wrongful_conviction

                    if audit:
                        if wrongful_conviction:
                            officer.balance -= Constants.officer_reprimand_amount  # officer
                            inter['officer_reprimand'] = Constants.officer_reprimand_amount
                            print('THE OFFICER WILL BE AUDITED $' + str(Constants.officer_reprimand_amount))
                        else:
                            print('NOTHING COMES OF AUDIT BECUASE CORRECT PERSON WAS CONVICTED')

                    officer.save()

                    # update intersection object
                    inter['convicted'] = convicted_pid
                    inter['officer_bonus'] = Constants.officer_intersection_payout
                    debug.append(interdebug)

                    # EVENT update save below
            else:
                # pass
                print('THERE ARE NO TOKENS IN INVESTIGATIONS THEREFORE THERE WILL BE NO CONVICTIONS')
                # EVENT update save below

            #EVENT FINAL
            # thisdict["intersections"] = intersections
            print('END TRANSACTION\n')

            #todo only send down if there are intersections. keep now to debuv
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'player_update',
                    'intersections': intersections,
                    'np_debug': debug, #wezza
                }
            )

    # Receive message from room group
    def player_update(self, event):
        intersections = event['intersections']
        np_debug = event['np_debug']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'intersections': intersections,
            'np_debug': np_debug,
        }))

    # Receive message from room group
    def investigation_update(self, event):
        investigation_count = event['investigation_count']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'investigation_update': investigation_count
        }))

