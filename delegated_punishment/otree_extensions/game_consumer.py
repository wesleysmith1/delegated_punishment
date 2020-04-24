from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from random import random, randrange
import numpy as np
from delegated_punishment.helpers import date_now_milli
from django.db import transaction

import logging
log = logging.getLogger(__name__)

from delegated_punishment.models import Player, Group, DefendToken, Constants, GameData, randomize_location


class GameConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['group_pk']
        self.room_group_name = self.room_name

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
        # print_padding = 25

        data_json = json.loads(text_data)

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        session_id = data_json['session_id']
        round_number = data_json['round_number']
        player = Player.objects.get(pk=player_id)

        event_time = date_now_milli()

        if data_json.get('balance'):

            group = Group.objects.get(pk=group_id)
            balance_update = group.balance_update(event_time)

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'balance_update',
                    'balance_update': balance_update,
                }
            )

        elif data_json.get('harvest'):
            # format
            # {}
            game_data_dict = {}
            player.harvest_status = harvest_status = data_json['harvest']['status']

            harvest_income = 0

            if player.harvest_status == 4:
                # increase balance
                harvest_income = player.income
                player.civilian_harvest()
                player.harvest_status = 0

            # print("PLAYER {} UPDATED HARVEST STATUS TO {}".format(player.pk, player.harvest_status))
            # print("PLAYER BALANCE: {}".format(player.balance))

            player.save()

            game_data_dict.update({
                "event_type": "harvest",
                "event_time": event_time,
                "production_inputs": harvest_status,  # don't update from player object in case it was reset to 0
                "player": player.id_in_group,
                "balance": player.balance,
                "harvest_income": harvest_income
            })

            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

        elif data_json.get('toggle'):
            # format
            # { harvest: bool }

            game_data_dict = {}

            toggle_status = data_json['toggle']

            # the player toggled screen losing progress on current harvest cycle
            if not toggle_status['harvest']:
                # reset harvest status
                player.harvest_status = 0
                player.harvest_screen = False
            else:
                player.harvest_screen = True
                game_data_dict.update({
                    "steal_reset": toggle_status["steal_reset"]
                })
                if player.map != 0:
                    victim = Player.objects.get(group_id=group_id, id_in_group=player.map)

                    victim.increase_roi(event_time, False)
                    victim.save()

                    game_data_dict.update({
                        "victim": victim.id_in_group,
                        "victim_roi": victim.roi,
                        "victim_balance": victim.balance,
                    })
                    # print("victim" + str(victim.id_in_group))

                    player.decrease_roi(event_time, True)
                else:
                    pass
                player.map = 0

            player.save()

            # print("player harvest screen value: {}".format(player.harvest_screen))

            game_data_dict.update({
                "event_type": "toggle",
                "event_time": event_time,
                "harvest_screen": player.harvest_screen,  # else steal
                "player": player.id_in_group,
                "player_roi": player.roi,
                "player_balance": player.balance,
            })
            # print(str(game_data_dict))
            GameData.objects.create(
                event_time=event_time,
                p=player.id,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

            # print("PLAYER TOGGLED HARVEST {}".format(toggle_status['harvest']))

        elif data_json.get('defend_token_drag'):
            # format
            # {
            #   number: 1-9,
            #   map: 0,
            #   x: 0,
            #   y: 0
            # }

            #save player location as 0 and send back confirmation
            dtoken = data_json['defend_token_drag']
            token_num = dtoken['number']

            try:
                token = DefendToken.objects.get(group_id=group_id, number=token_num)
            except DefendToken.DoesNotExist:
                token = None
                # print('ERROR: NO TOKEN WAS FOUND')

            # check if token was removed from investigations
            investigation_change = False
            if token.map == 11:
                investigation_change = True

            # set token to no map while it is being dragged
            token.map = token.x = token.y = token.x2 = token.y2 = 0
            token.save()

            game_data_dict = {
                "event_type": "defend_token_drag",
                "event_time": event_time,
                "token_number": token_num,
                "map": 0,
                "player": player.id_in_group,
            }
            # token count is calculated so we save gamedata here
            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                jdata=game_data_dict
            )

            # print('TOKEN WAS DRAGGED AND PROP SET TO ' + str(token.map))

            # update users with investigation token count
            if investigation_change:
                token_count = DefendToken.objects.filter(group_id=group_id, map=11).count()
                # print('TOTAL TOKEN COUNT ' + str(token_count))

                # send token count to group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'investigation_update',
                        'investigation_count': token_count,
                    }
                )
        elif data_json.get('steal_token_timeout'):
            # format
            # {
            #     x: o,
            #     y: o,
            #     map: 0
            # }

            # get token and save it's location as 0
            location = data_json['steal_token_timeout']['steal_location']

            game_data_dict = {
                "event_type": "steal_token_timeout",
                "player": player.id_in_group,
                "event_time": event_time,
                "steal_reset": location,
            }

            # update roi for stealing player and victim of the theft.
            # update victim roi
            victim = Player.objects.get(group_id=group_id, id_in_group=player.map) #todo add try catch here

            # print('PLAYER WAS STEALING FROM PLAYER ' + str(victim.pk))
            victim.increase_roi(event_time, False)
            victim.save()

            game_data_dict.update({
                "victim": victim.id_in_group,
                "victim_roi": victim.roi,
                "victim_balance": victim.balance
            })

            # update player roi
            player.decrease_roi(event_time, True)

            game_data_dict.update({
                "player_roi": player.roi,
                "player_balance": player.balance,
            })

            player.x = player.y = player.map = 0
            player.save()

            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

        elif data_json.get('steal_token_drag'):
            # format
            # {
            #     x: o,
            #     y: o,
            #     map: 0
            # }
            # print('LOCATION TOKEN WAS DRAGGED')
            #get token and save it's location as 0

            game_data_dict = {
                "event_type": "steal_token_drag",
                "player": player.id_in_group,
                "event_time": event_time,
                "map": 0,
            }

            # update roi for stealing player and victim of the theft.
            if player.map > 0:
                # update victim roi
                victim = Player.objects.get(group_id=group_id, id_in_group=player.map)
                # print('PLAYER WAS STEALING FROM PLAYER ' + str(victim.pk))
                victim.increase_roi(event_time, False)
                victim.save()

                game_data_dict.update({
                    "victim": victim.id_in_group,
                    "victim_roi": victim.roi,
                    "victim_balance": victim.balance
                })

                # update player roi
                player.decrease_roi(event_time, True)
                game_data_dict.update({
                    "player_roi": player.roi,
                    "player_balance": player.balance,
                })

            else:
                pass
                # print('PLAYER WAS NOT STEALING BEFORE')

            player.x = player.y = player.map = 0
            player.save()
            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

            # print('LOCATION DRAG TRANSCATION COMPLETE AND map SET TO ' + str(player.map))

        elif data_json.get('defend_token_reset'):
            token_number = data_json['defend_token_reset']['number']
            token_slot = data_json['defend_token_reset']['slot']

            # todo: should we save the defendtoken slot here?
            # DefendToken.objects.get(group_id=group_id, number=token_number, ).update(slot=token_slot)

            game_data_dict = {
                "event_type": "defend_token_reset",
                "event_time": event_time,
                "player": player.id_in_group,
                "token_number": token_number,
                "defend_reset": token_slot,
            }
            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

        elif data_json.get('steal_token_reset'):

            game_data_dict = {
                "event_type": "steal_token_reset",
                "event_time": event_time,
                "player": player.id_in_group,
                "steal_reset": data_json["steal_token_reset"]["steal_location"]
            }
            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

        elif data_json.get('investigation_update'):
            # format
            # {
            #   number: 1-9,
            #   map: 0,
            #   x: 0,
            #   y: 0
            # }

            # set location to prop to 11 for investigation
            i_token = data_json['investigation_update']
            token_num = i_token['number']

            try:
                token = DefendToken.objects.get(group_id=group_id, number=token_num)
            except DefendToken.DoesNotExist:
                print('ERROR INVESTIGATION=: token not found')
                token = None

            token.x = token.y = token.x2 = token.y2 = -1
            token.map = 11
            token.last_updated = event_time
            token.save()
            # get investigation token count
            token_count = DefendToken.objects.filter(group_id=group_id, map=11).count()
            # print('TOTAL TOKEN COUNT ' + str(token_count))

            game_data_dict = {
                "event_type": "investigation_update",
                "event_time": event_time,
                "player": player.id_in_group,
                "token_number": token_num,
                "investigation_count": token_count,
            }
            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

            # send token count to group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'investigation_update',
                    'investigation_count': token_count,
                }
            )

        elif data_json.get('period_update'):
            pu = data_json['period_update']

            game_data_dict = {
                "player": player.id_in_group
            }

            if pu.get('period_start'):
                game_data_dict.update({
                    'event_time': event_time,
                    'event_type': 'round_start'
                })

                GameData.objects.create(
                    event_time=event_time,
                    p=player.id_in_group,
                    g=group_id,
                    s=session_id,
                    round_number=round_number,
                    jdata=game_data_dict
                )

                Group.objects.filter(id=group_id).update(game_start=event_time)

                # inform channel of round start
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'round_start',
                        'start': True,
                    }
                )
            elif pu.get('period_end'):
                # todo: period end will likely be a scheduled event that lets a players know the round is over

                end_time = date_now_milli()

                game_data_dict.update({
                    'event_time': end_time,
                    'event_type': 'period_end'
                })

                # final calculation of player balances for results page
                group = Group.objects.get(pk=group_id)
                players = group.get_players()
                for p in players:
                    p.balance = p.get_balance(end_time)
                    p.save()

                GameData.objects.create(
                    event_time=end_time,
                    p=player.id_in_group,
                    g=group_id,
                    s=session_id,
                    round_number=round_number,
                    jdata=game_data_dict
                )

                # inform players that round is over
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'round_over',
                        'round_over': None,
                    }
                )

            elif pu.get('period_results'):
                round_results = dict(balance=player.balance)

                # send token count to group
                self.send(text_data=json.dumps({
                    'round_results': round_results
                }))

        else:
            # the following cases require more computation and send data down to all players

            game_data_dict = {}

            # root level variables
            map = -1
            x = -1
            y = -1
            intersections = []

            if data_json.get('defend_token_update'):
                token_update = data_json['defend_token_update']
                token_num = token_update['number']

                x = token_update['x']
                y = token_update['y']
                map = token_update['map']

                try:
                    token = DefendToken.objects.get(group_id=group_id, number=token_num)
                except DefendToken.DoesNotExist:
                    token = None
                    # print('ERROR: NO TOKEN WAS FOUND')

                token.map = map
                token.x = x
                token.y = y
                token.x2 = x + Constants.defend_token_size
                token.y2 = y + Constants.defend_token_size
                token.save()

                game_data_dict.update({
                    "event_type": "defend_token_update",
                    "player": player.id_in_group,
                    "event_time": event_time,
                    "token_number": token_num,
                    "map": token.map,
                    "token_x": token.x,
                    "token_y": token.y,
                    "token_x2": token.x2,
                    "token_y2": token.y2,
                })

                players_in_prop = Player.objects.filter(group_id=group_id, map=token.map, id_in_group__gt=1)  # todo check why this was changing the roi and updating the balance for the officer incorrectly?

                # print("{} --{}-- map: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(print_padding), token_num, token.map, token.x, token.y))
                # print("THERE ARE {} PLAYERS IN map {}".format(len(players_in_prop), token.map))

                if players_in_prop:
                    for p in players_in_prop:

                        # print("{} --{}-- map: {} X: {:6.2f} Y: {:6.2f}".format('PLAYER'.ljust(print_padding), p.pk, p.map, p.x, p.y))

                        if token.x <= p.x <= token.x2 and \
                                token.y <= p.y <= token.y2:

                            # print('{} {} AND PLAYER {}'.format('INTERSECTION BETWEEN TOKEN'.ljust(print_padding), token.number, p.pk))

                            # update culprit
                            p.decrease_roi(event_time, True)

                            # update victim
                            victim = Player.objects.get(group_id=group_id, id_in_group=p.map) # map here represents the player id in group since they line up in every group/game
                            victim.increase_roi(event_time, False)
                            victim.save()

                            # we do this here so we don't reset player data to -1 in which case the ui can't display intersection dots.
                            # create intersection data
                            data = {
                                # police log info
                                'event_time': event_time,

                                'culprit': p.id_in_group,
                                'culprit_y': p.y,
                                'culprit_x': p.x,
                                'culprit_balance': p.balance,
                                'map': p.map, #?
                                'victim': victim.id_in_group,
                                'victim_roi': victim.roi,
                                'victim_balance': victim.balance,
                                # 'token_number': token.number,
                                'token_x': token.x,
                                'token_y': token.y,
                                'token_x2': token.x2,
                                'token_y2': token.y2,
                                'steal_reset': randomize_location()
                            }

                            # update player info
                            p.map = 0
                            p.x = p.y = -1
                            p.save()
                            # print("PLAYER {} UPDATED AT {:6.2f}".format(p.pk, p.last_updated))

                            intersections.append(data)

            elif data_json.get('steal_token_update'):

                steal_location = data_json['steal_token_update']

                x = steal_location['x']
                y = steal_location['y']
                map = steal_location['map']

                player.x = x
                player.y = y
                player.map = map

                game_data_dict.update({
                    "event_type": "steal_token_update",
                    "event_time": event_time,
                    "player": player.id_in_group,
                    "culprit": player.id_in_group,
                    "map": map,
                    "token_x": x,
                    "token_y": y,
                })

                # print("{} -- {} -- map: {} X: {:6.2f} Y: {:6.2f}".format('CIVILIAN LOCATION UPDATE'.ljust(print_padding), player.pk, player.map, player.x, player.y))

                # check for intersections
                tokens = DefendToken.objects.filter(group_id=group_id, map=player.map).order_by('last_updated')
                # print('THERE ARE ' + str(len(tokens)) + ' TOKENS IN THIS map')
                # print("THERE ARE {} TOKENS IN map {}".format(len(tokens), player.map))

                if tokens:
                    for token in tokens:
                        # print("{} -- {}-- map: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(print_padding), token.number, token.map, token.x, token.y))
                        if token.x <= player.x <= token.x2 and token.y <= player.y <= token.y2:
                            # print('\t\tINTERSECTION')

                            # create intersection data
                            data = {
                                # police log info
                                'event_time': event_time,

                                'culprit': player.id_in_group,
                                'map': map,  # ?
                                'token_number': token.number,

                                # data for displaying intersections
                                'culprit_y': y,
                                'culprit_x': x,

                                'token_x': token.x,
                                'token_y': token.y,
                                'token_x2': token.x2,
                                'token_y2': token.y2,
                                'steal_reset': randomize_location()
                            }
                            intersections.append(data)

                            # update player info
                            player.map = 0
                            player.x = 0
                            player.y = 0

                            break

                # if there was no intersection -> update the roi of player and victim
                if player.map != 0:
                    # update player roi
                    player.increase_roi(event_time, True)

                    game_data_dict.update({
                        "culprit_roi": player.roi,
                        "culprit_balance": player.balance,
                    })

                    # get victim object and update roi
                    victim = Player.objects.get(group_id=group_id, id_in_group=player.map)
                    victim.decrease_roi(event_time, False)
                    victim.save()

                    game_data_dict.update({
                        "victim": victim.id_in_group,
                        "victim_roi": victim.roi,
                        "victim_balance": victim.balance,
                    })
                # else:
                    # player.last_updated = event_time

                # print("PLAYER {} UPDATED AT {:6.2f}".format(player.pk, player.last_updated))
                player.save()

            num_investigators = DefendToken.objects.filter(group_id=group_id, map=11).count()
            # print('INVESTIGATION TOKEN COUNT: ' + str(num_investigators))

            # intersection objects for Game Data
            game_data_intersections = []

            # increased for each investigated intersection and civilian fine
            officer_bonus = 0
            civilian_fine = 0

            for inter in intersections:
                # print(inter)

                # print('\t\tSTARTING NUMPY CALCULATIONS')
                culprit = inter["culprit"]
                innocent = inter["map"]  # also victim

                if num_investigators >= Constants.a_max:
                    innocent_prob = 0
                    guilty_prob = Constants.beta
                else:
                    # innocent_prob = 1 / 4 - num_investigators / 20
                    innocent_prob = (6 - num_investigators) * (9/240)
                    # guilty_prob = 1 / 4 + num_investigators / 10
                    guilty_prob = (2+num_investigators) * (9/80)

                multi = [0, innocent_prob, innocent_prob, innocent_prob, innocent_prob, innocent_prob, 1-Constants.beta]

                # subtract 1 for 0 based index
                multi[culprit - 1] = guilty_prob
                multi[innocent - 1] = 0
                # print('\t\tMULTI' + str(multi))

                result = np.random.multinomial(1, multi, 1)[0]

                # which player was convicted from result
                for index, i in enumerate(result):  # search array for result ex; [0,1,0,0,0,0,0]
                    if i == 1:

                        if index == Constants.players_per_group:
                            # nobody punished, no officer bonus
                            convicted_pid = None
                        else:
                            # no need to add calculable value to game data
                            convicted_pid = int(index + 1)
                        break

                # print('CONVICTED PLAYER: ' + str(convicted_pid))
                if convicted_pid:
                    convicted_player = Player.objects.get(group_id=group_id, id_in_group=convicted_pid)
                    convicted_player.civilian_fine()
                    convicted_player.save()

                    # increment counter
                    civilian_fine += 1

                    # check if guilty player was convicted
                    wrongful_conviction = True
                    if convicted_pid == culprit:
                        # print('THE CORRECT PLAYER WAS CONVICTED')
                        wrongful_conviction = False
                    else:
                        pass
                        # print('THE WRONG PLAYER WAS CONVICTED')

                    # UPDATE OFFICER BALANCE
                    if player.id_in_group == 1:
                        officer = player
                    else:
                        officer = Player.objects.get(group_id=group_id, id_in_group=1)
                    officer.officer_bonus()

                    # increment counter
                    officer_bonus += 1

                    audit = np.random.binomial(1, Constants.officer_review_probability)
                    # print('HERE IS THE AUDIT RESULT: ' + str(audit))

                    officer_reprimand = 0

                    if audit:
                        if wrongful_conviction:
                            officer.officer_reprimand()
                            officer_reprimand = Constants.officer_reprimand_amount

                    officer.save()

                    # update intersection object
                    inter.update({
                        "innocent": innocent,  # ?
                        "multi_input": multi,
                        "multi_result": str(result),
                        "guilty": convicted_pid,
                        "wrongful_conviction": wrongful_conviction,
                        "audit": str(audit),

                        # notification log info
                        "officer_bonus": officer.income,
                        "officer_reprimand": officer_reprimand,
                    })

                    game_data_intersections.append(inter)

                else:
                    game_data_intersections.append(inter)

            # send down intersections
            if len(game_data_intersections) > 0:

                # update group counters
                Group.intersection_update(group_id, officer_bonus, civilian_fine)

                game_data_dict["intersections"] = game_data_intersections

                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'intersections_update',
                        'intersections': intersections,
                    }
                )

            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )

    # Receive message from room group
    def intersections_update(self, event):
        intersections = event['intersections']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'intersections': intersections,
        }))

    # Receive message from room group
    def investigation_update(self, event):
        investigation_count = event['investigation_count']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'investigation_update': investigation_count
        }))

    def balance_update(self, event):
        balance_update = event['balance_update']

        self.send(text_data=json.dumps({
            'balance': balance_update
        }))

    def round_over(self, event):
        self.send(text_data=json.dumps({
            'round_over': True
        }))

    def round_start(self, event):
        self.send(text_data=json.dumps({
            'round_start': True
        }))
