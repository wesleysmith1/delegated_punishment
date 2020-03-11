from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from delegated_punishment.helpers import date_now_milli

from delegated_punishment.models import Player, Group, GameData, Constants

class GameSyncConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = f"sync_{self.scope['url_route']['kwargs']['group_pk']}"
        self.room_group_name = self.room_name

        print('CONNECTED')

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
        # print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        player = Player.objects.get(pk=player_id)
        group = Group.objects.get(pk=group_id)
        round_number = data_json['round_number']

        if data_json.get('join'):
            # player is now ready

            if not player.ready:
                print(f"PLAYER {player_id} IS NOW READY")
                player.ready = True
                player.save()
                group.players_ready += 1
                group.save()
                print(f"GROUP {group_id} NOW HAS {group.players_ready} READY")
                time_remaining = group.check_game_status(date_now_milli())

                if time_remaining:
                    print(f"GROUP HAS ALL ARRIVED")
                    async_to_sync(self.channel_layer.group_send)(
                        self.room_group_name,
                        {
                            'type': 'start_game',
                            'start_time': time_remaining
                        }
                    )
            else:
                # game already started
                time_remaining = group.check_game_status(date_now_milli())

                self.send(text_data=json.dumps({
                    'start_time': time_remaining
                }))

        elif data_json.get('period_end'):
            event_time = date_now_milli()
            game_data_dict = {
                'event_time': event_time,
                'event_type': 'period_end'
            }
            """Officer sends up period end"""
            GameData.objects.create(
                event_time=event_time,
                g=group_id,
                r=round_number,
                jdata=game_data_dict
            )

    # Receive message from room group
    def start_game(self, event):
        start_time = event['start_time']
        # Start game after all players are synced
        self.send(text_data=json.dumps({
            'start_game': True,
            'start_time': start_time
        }))
