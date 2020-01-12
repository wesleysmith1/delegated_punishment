from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from random import random
import numpy as np

from delegated_punishment.models import Player, Group, OfficerToken


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

        PADDING_SIZE = 10
        PADDING_SIZE_LONG = 25

        # todo: save block size somewhere else
        block_size = 50

        data_json = json.loads(text_data)
        # print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        player = Player.objects.get(pk=player_id)
        group = Group.objects.get(pk=group_id) # can we delete this? is it more efficient to search my pk rather than django object

        intersections = []

        if data_json.get('token'):
            token_update = data_json['token']
            token_num = token_update['number']
            # token = OfficerToken.objects.filter(group=group, number=token_num)[0] #this breaks sucka
            try:
                token = OfficerToken.objects.get(group=group, number=token_num)
            except OfficerToken.DoesNotExist:
                token = None
                print('NO TOKEN WAS FOUND BRAP BRAP')

            # if token:
            #     print('TOKEN ON PROPERTY ' + str(token.property))

            token.property = token_update['property']
            if token.property == 11:
                print("TOKEN --{}-- SET TO INVESTIGATE".format(token_num))
                token.save()
            else:
                token.x = token_update['x']
                token.y = token_update['y']
                token.save()
                print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(PADDING_SIZE_LONG), token_num, token.property, token.x, token.y))
                players_in_prop = Player.objects.filter(group=group, property=token.property)
                print("THERE ARE {} PLAYERS IN PROPERTY {}".format(len(players_in_prop), token.property))

                if players_in_prop:
                    for p in players_in_prop:
                        # intersections = Dict
                        print("{} --{}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('PLAYER'.ljust(PADDING_SIZE_LONG), p.pk, p.property, p.x, p.y))
                        if token.x <= p.x <= (token.x + block_size) and token.y <= p.y <= (token.y + block_size):
                            print('{} {} AND PLAYER {}'.format('INTERSECTION BETWEEN TOKEN'.ljust(PADDING_SIZE_LONG),token.number, p.pk))

                            # create intersection data
                            data = {'player': p.pk, 'y': p.y, 'x': p.x, 'property': p.property, 'token': token.number}
                            intersections.append(data)

                            # update player info
                            p.property = 0
                            p.x = None
                            p.y = None
                            p.save()

                    # if intersections:

            # token.x =
        # if data_json.get('harvest'):
        #     harvest_status = data_json['harvest']
        #     player.harvest_status = harvest_status['current']
        #     if player.harvest_status == 4:
        #         player.balance = player.balance+1
        #         player.harvest_status = 0
        #     player.save()
        if data_json.get('steal'):
            steal_location = data_json['steal']
            player.x = steal_location['x']
            player.y = steal_location['y'] #todo: add this later so we only save once, not here then again after intersection
            player.property = steal_location['property']
            player.save()
            print("{} -- {} -- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('CIVILIAN LOCATION UPDATE'.ljust(PADDING_SIZE_LONG), player.pk, player.property, player.x, player.y))
            # check for intersections
            tokens = OfficerToken.objects.filter(group=group, number=player.property)
            print('THERE ARE ' + str(len(tokens)) + ' TOKENS IN THIS PROPERTY')
            print("THERE ARE {} TOKENS IN PROPERTY {}".format(len(tokens), player.property))

            if tokens:
                for token in tokens:
                    print("{} -- {}-- PROPERTY: {} X: {:6.2f} Y: {:6.2f}".format('TOKEN'.ljust(PADDING_SIZE_LONG), token.number, token.property, token.x, token.y))
                    if token.x <= player.x <= (token.x + block_size) and token.y <= player.y <= (token.y + block_size):
                        print('\t\tINTERSECTION')

                        # create intersection data
                        data = {'player': player.pk, 'y': player.y, 'x': player.x, 'property': player.property, 'token': token.number}
                        intersections.append(data)

                        # update player info
                        player.property = 0
                        player.x = None
                        player.y = None
                        player.save()

        if len(intersections) > 0:
            num_investigators = OfficerToken.objects.filter(group=group, number=11)
            print('INVESTIGATION TOKEN COUNT: ' + str(len(num_investigators)))
            if len(num_investigators) > 0:
                for inter in intersections:
                    # MULTINULI PUNISH?
                    guilty = inter.player
                    innocent = inter.property
                    # police =
                    innocent_prob = 1 / 3 - num_investigators / 30
                    guilty_prob = 1 / 3 + 2 * num_investigators / 30
                    multi = [0, innocent_prob, innocent_prob, innocent_prob, innocent_prob]
                    multi[guilty] = guilty_prob
                    print('MULTI' + multi)
                    # WILL WE AUDIT?

            else:
                # todo: do we record but don't punish here?
                print('THERE ARE NO TOKENS IN INVESTIGATIONS')

        print('END TRANSACTION\n')

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

    def test_update(self, event):
        # message = event['message']

        player = Player.objects.first()
        player.balance = 1
        player.save()

        player = Player.objects.last()
        player.balance = 100
        player.save()

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'test': str(random() * 1000)
        }))
