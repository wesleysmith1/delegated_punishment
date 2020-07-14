from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from delegated_punishment.helpers import date_now_milli

from delegated_punishment.models import Player, Group, GameData, Constants

class GameSyncConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = f"sync_{self.scope['url_route']['kwargs']['group_pk']}"
        self.room_group_name = self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        data_json = json.loads(text_data)
        print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        player = Player.objects.get(pk=player_id)
        group = Group.objects.get(pk=group_id)
        round_number = data_json['round_number']

        if data_json.get('ready'):
            # player is now ready

            player.ready = True
            player.save()

            print('how does this look')

            ready_players = Player.objects.filter(group_id=group_id, ready=True)

            print(f'NUMBER OF PLAYERS {len(ready_players)}')
            print(f'CONSTANTS: {Constants.players_per_group}')



            if len(ready_players) == Constants.players_per_group:
                # inform host player that game needs to start
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'players_ready',
                    }
                )

        elif data_json.get('round_end'):
            event_time = date_now_milli()
            game_data_dict = {
                'event_time': event_time,
                'event_type': 'round_end'
            }
            """Officer sends up period end"""
            GameData.objects.create(
                event_time=event_time,
                g=group_id,
                r=round_number,
                jdata=game_data_dict
            )

    # Receive message from room group
    def players_ready(self, event):
        print('hi')
        # Start game after all players are synced
        self.send(text_data=json.dumps({
            'players_ready': True,
        }))
