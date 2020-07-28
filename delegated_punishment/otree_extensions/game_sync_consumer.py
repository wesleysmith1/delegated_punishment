from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import logging
log = logging.getLogger(__name__)

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

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        player = Player.objects.get(pk=player_id)

        if data_json.get('ready'):
            # mark player as ready
            player.ready = True
            player.save()

            log.info(f"player {player_id} ready")

        elif data_json.get('sync_status'):

            # host polls to check if all players are ready
            ready_players = len(Player.objects.filter(group_id=group_id, ready=True))
            log.info(f"host {player_id} is checking sync status. status is {ready_players}")

            if ready_players == Constants.players_per_group:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'sync_status',
                    }
                )

    # Inform players that players have arrived so host can signal game start
    def sync_status(self, event):
        self.send(text_data=json.dumps({
            'sync_status': True,
        }))
