from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from random import random

from bargaining.models import Player, Group

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = 'room'
        self.room_group_name = 'group'
        player = Player.objects.first()
        player.lives = 1
        player.save()

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
        player = Player.objects.first()
        player.lives = 1
        player.save()
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        x = Player.objects.all()
        y = Group.objects.all()
        player = Player.objects.first()
        player.lives = 1
        player.save()
        # player = Player.objects.first()
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'player_update',
                'message': str(random())
            }
        )
    
    # Receive message from room group
    def player_update(self, event):
        message = event['message']

        # player = Player.objects.first()
        # player.lives = 1
        # player.save()
        # player = Player.objects.first()
        # player.lives = 2
        # player.save()
        # player = Player.objects.first()
        # player.lives = 3
        # player.save()
        player = Player.objects.first()
        player.lives = 1
        player.save()

        # can we send async code here if any updates to individual players


        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': str(random())
        }))

    
    