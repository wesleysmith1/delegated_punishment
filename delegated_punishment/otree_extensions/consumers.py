from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from random import random

from delegated_punishment.models import Player, Group

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = 'room'
        self.room_group_name = 'group'

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
        data_json = json.loads(text_data)
        # x = Player.objects.all()
        # y = Group.objects.all()
        # player = Player.objects.first()
        # player.balance = 1
        # player.save()
        # player = Player.objects.first()
        # Send message to room group

        print('YOU HAVE ARRIVED')
        print(data_json)

        if data_json.get('test'):
            print(str(random()*1000))
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'test_update',
                    'message': str(random())
                }
            )
        else:
            print('MAKING AN UPDATE CALL')
            location = data_json['location']
            p_id = data_json['p_id']

            player = Player.objects.get(pk=p_id)
            players_in_location = Player.objects.filter(location=location)
            busted_player_ids = []

            if player.id_in_group == 1:
                print('PLAYER IS COP')         
                #player is it
                if players_in_location:
                    
                    for p in players_in_location:
                        busted_player_ids.append(p.id)
                        p.location = -1
                        p.balance = p.balance-1
                        player.balance+=1

                    for p in players_in_location:
                        p.save()
                else:
                    print('THERE WERE NO PLAYERS IN THE LOCATION DUMBASS')

                player.location = location
                player.save()
            else:
                print('THIS IS NOT A COP')
                #player is not it
                cop = Player.objects.filter(id_in_group=1)[0]
                if cop.location == location:
                    player.balance = player.balance-1
                    busted_player_ids.append(player.id)
                    cop.balance = cop.balance+1
                    cop.save()
                else:
                    player.location = location
                    player.balance = player.balance+1
                    # self.send_json(text_data="none")
                    
                player.location = location
                player.save()

            zzz = Player.objects.all()
            player_data = {}
            for p in zzz:
                player_data[p.id] = p.balance
                
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'player_update',
                    'ids': busted_player_ids,
                    'player_data': player_data
                }
            )


    
    # Receive message from room group
    def player_update(self, event):
        ids = event['ids']
        player_data = event['player_data']

        # player = Player.objects.first()
        # player.balance = 1
        # player.save()
        # player = Player.objects.first()
        # player.balance = 2
        # player.save()
        # player = Player.objects.first()
        # player.balance = 3
        # player.save()
        # player.balance = 1
        # player.save()

        # can we send async code here if any updates to individual players


        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'ids':ids,
            'data': player_data
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
            'test': str(random()*1000)
        }))

    
    