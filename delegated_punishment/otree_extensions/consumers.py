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
        print("DISCONNECTING")
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

        PADDING_SIZE_LONG = 25

        data_json = json.loads(text_data)
        print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id'] #todo make this player_id_in_group?
        player = Player.objects.get(pk=player_id)
        group = Group.objects.get(pk=group_id) # can we delete this object? is it more efficient to search my pk rather than django object

        intersections = []

        if data_json.get('balance'):
            current_balance = player.get_balance()
            current_roi = player.roi

            # Send message to WebSocket
            self.send(text_data=json.dumps({
                'balance': current_balance,
                'roi': current_roi
            }))
        else:

            if data_json.get('token'):
                token_update = data_json['token']
                token_num = token_update['number']

                try:
                    token = OfficerToken.objects.get(group=group, number=token_num) # todo this will error if there are more than one result
                except OfficerToken.DoesNotExist:
                    token = None
                    print('NO TOKEN WAS FOUND')
                    # todo: research how we should exit here to prevent executing any more code

                token.property = token_update['property']
                if token.property == 11:
                    print("TOKEN --{}-- SET TO INVESTIGATE".format(token_num))
                    token.x = -1
                    token.y = -1
                    token.save()
                else:
                    token.x = token_update['x']
                    token.y = token_update['y']
                    token.save()
                    players_in_prop = Player.objects.filter(group=group, property=token.property)

                    print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(PADDING_SIZE_LONG), token_num, token.property, token.x, token.y))
                    print("THERE ARE {} PLAYERS IN PROPERTY {}".format(len(players_in_prop), token.property))

                    if players_in_prop:
                        for p in players_in_prop:
                            # intersections = Dict
                            print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('PLAYER'.ljust(PADDING_SIZE_LONG), p.pk, p.property, p.x, p.y))
                            if token.x <= p.x <= (token.x + Constants.officer_token_size) and token.y <= p.y <= (token.y + Constants.officer_token_size):

                                print('{} {} AND PLAYER {}'.format('INTERSECTION BETWEEN TOKEN'.ljust(PADDING_SIZE_LONG), token.number, p.pk))

                                # create intersection data
                                data = {'player': p.pk, 'y': p.y, 'x': p.x, 'property': p.property, 'token': token.number}
                                intersections.append(data)

                                # todo: update criminal and victim players roi here
                                # update robber roi
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
                                p.x = -1 #todo consider making this none and fixing logging issue
                                p.y = -1
                                p.last_updated = date_now_milli()
                                p.save()
                                print("PLAYER {} UPDATED AT {:6.2f}".format(p.pk, p.last_updated))

            if data_json.get('harvest'):
                harvest_status = data_json['harvest']
                player.harvest_status = harvest_status['status']

                if player.harvest_status == 4:
                    # increase balance
                    player.balance = player.balance + Constants.civilian_income
                    player.harvest_status = 0

                print("PLAYER {} UPDATED HARVEST STATUS TO {}".format(player.pk, player.harvest_status))
                print("PLAYER BALANCE: {}".format(player.balance))
                player.save()

            if data_json.get('steal'):

                steal_location = data_json['steal']
                player.x = steal_location['x']
                player.y = steal_location['y'] #todo: add this later so we only save once, not here then again after intersection
                player.property = steal_location['property']

                #todo: if player is in own property we should just save their property=0, x=-100, y=-100, update roi if they were in another property before, last_updated
                is_in_own_property = player.property == player.id_in_group

                # player.save()
                print("{} -- {} -- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('CIVILIAN LOCATION UPDATE'.ljust(PADDING_SIZE_LONG), player.pk, player.property, player.x, player.y))

                # check for intersections
                tokens = OfficerToken.objects.filter(group=group, property=player.property)
                print('THERE ARE ' + str(len(tokens)) + ' TOKENS IN THIS PROPERTY')
                print("THERE ARE {} TOKENS IN PROPERTY {}".format(len(tokens), player.property))

                if tokens:
                    for token in tokens:
                        print("{} -- {}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(PADDING_SIZE_LONG), token.number, token.property, token.x, token.y))
                        if token.x <= player.x <= (token.x + Constants.officer_token_size) and token.y <= player.y <= (token.y + Constants.officer_token_size):
                            print('\t\tINTERSECTION')

                            # create intersection data
                            data = {'player': player.pk, 'y': player.y, 'x': player.x, 'property': player.property, 'token': token.number}
                            intersections.append(data)

                            # update player info
                            player.property = 0
                            player.x = None # todo: this None could break the logging
                            player.y = None

                            break
                            # player.save() # todo: we will need to hold off on saving here. This is preventing civilians from getting caught twice

                # if there was no intersection we update the roi of player and victim
                if player.property != 0:
                    # update player roi
                    player.increase_roi()
                    # get victim object and update roi
                    victim = Player.objects.get(group=group, id_in_group=player.property)
                    victim.decrease_roi()
                    victim.last_updated = date_now_milli()
                    victim.save()

                player.last_updated = date_now_milli()
                print("PLAYER {} UPDATED AT {:6.2f}".format(player.pk, player.last_updated))
                player.save()

            num_investigators = len(OfficerToken.objects.filter(group=group, property=11))
            print('INVESTIGATION TOKEN COUNT: ' + str(num_investigators))
            if num_investigators > 0:
                for inter in intersections:
                    # MULTINULI PUNISH?
                    print(inter)
                    print('\t\tSTARTING NUMPY CALCULATIONS')
                    guilty = inter['player']
                    innocent = inter['property']
                    # police = 0
                    innocent_prob = 1 / 3 - num_investigators / 30
                    guilty_prob = 1 / 3 + 2 * num_investigators / 30
                    multi = [0, innocent_prob, innocent_prob, innocent_prob, innocent_prob]
                    # subtract 1 for 0 based index
                    multi[guilty - 1] = guilty_prob
                    multi[innocent - 1] = innocent_prob
                    print('\t\tMULTI' + str(multi))

                    result = np.random.multinomial(1, multi, 1)[0]
                    convicted_player = -1
                    # determine which player was convicted from result
                    for i in range(len(result)):  # search array for result ex; [0,1,0,0,0]
                        if result[i] == 1:
                            convicted_pid = int(i + 1)
                            break
                    print('\t\tHERE IS THE NUMPY RESULT ' + str(result))

                    # updated convicted plater balance
                    print('CONVICTED PLAYER: ' + str(convicted_pid))
                    convicted_player = Player.objects.get(group=group, id_in_group=convicted_pid)
                    convicted_player.balance -= Constants.civilian_conviction_amount
                    convicted_player.save()

                    # CALCULATE IF INTERSECTION WILL BE REVIEWED?
                    audit = np.random.binomial(1, Constants.officer_review_probability)  # todo check the syntax on this
                    print('HERE IS THE AUDIT RESULT: ' + str(audit))

                    # UPDATE OFFICER BALANCE
                    officer = Player.objects.get(group=group, id_in_group=1)
                    officer.balance += Constants.officer_intersection_payout

                    if audit:
                        officer.balance -= Constants.officer_reprimand_amount
                    officer.save()

                    # update intersection object
                    inter['convicted'] = convicted_pid
                    inter['officer_bonus'] = Constants.officer_intersection_payout
                    inter['officer_reprimand'] = Constants.officer_reprimand_amount
                else:
                    print('THERE ARE NO TOKENS IN INVESTIGATIONS')

            print('END TRANSACTION\n')

            #todo do we have to return something here? like if a harvest confirmation?
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'player_update',
                    'intersections': intersections,
                }
            )

    # Receive message from room group
    def player_update(self, event):
        intersections = event['intersections']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'intersections': intersections
        }))

