from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import logging
log = logging.getLogger(__name__)

from delegated_punishment.helpers import date_now_milli

from delegated_punishment.models import Player, Group, GameData, Constants, GameStatus

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

        if data_json.get('player_ready'):
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

        elif data_json.get('validate_players'):
            # This should only get called during round
            group = Group.objects.get(id=group_id)
            if group.game_status != GameStatus.ACTIVE:
                return

            time = date_now_milli() - 3

            invalid_players = Player.objects.filter(group_id=group_id, last_updated__lt=time, map__gt=0)

            for player in invalid_players:
                player.stop_stealing()

        elif data_json.get('round_info'):
            # notify players to display round info modal
            group_id = data_json['group_id']

            group = Group.objects.get(id=group_id)
            group.game_status = GameStatus.INFO
            group.save()
            log.info(f'group {group_id} game_status updated to {Group.objects.get(id=group_id).game_status}')

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'round_info',
                }
            )

        elif data_json.get('round_active'):
            # Round start GameData object created. players notified game has started

            event_time = date_now_milli()
            round_number = data_json['round_number']
            session_id = data_json['session_id']
            player_id = data_json['player_id']
            group_id = data_json['group_id']

            game_data_dict = {
                'event_time': event_time,
                'event_type': 'round_start',
                'player': player_id,
            }

            # set game status to active
            group = Group.objects.get(id=group_id)
            group.game_status = GameStatus.ACTIVE
            group.save()
            log.info(f'group {group_id} game_status updated to {Group.objects.get(id=group_id).game_status}')

            GameData.objects.create(
                event_time=event_time,
                p=player.id_in_group,
                g=group_id,
                s=session_id,
                round_number=round_number,
                jdata=game_data_dict
            )
            # inform players round has started
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'round_active',
                }
            )

        elif data_json.get('round_timeout'):
            # notify players that round is over. no more events should be sent up.
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'round_timeout',
                }
            )

        elif data_json.get('round_end'):

            end_time = date_now_milli()
            round_number = data_json['round_number']
            session_id = data_json['session_id']
            player_id = data_json['player_id']
            group_id = data_json['group_id']

            game_data_dict = {
                'event_time': end_time,
                'event_type': 'round_end',
                'player': player_id,
            }

            # set game status to results
            group = Group.objects.get(id=group_id)
            group.game_status = GameStatus.RESULTS
            group.save()
            log.info(f'group {group_id} game_status updated to {Group.objects.get(id=group_id).game_status}')

            # inform players that round is over
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'round_end',
                    'round_end': None,
                }
            )

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

        elif data_json.get('round_results'):

            # get title for results modal
            group = Group.objects.get(pk=group_id)
            title = 'Round Results'
            if group.is_tutorial():
                title = "Tutorial results"

            round_results = dict(balance=player.balance, title=title)

            # civilian_fine_total = models.IntegerField(initial=0)
            # officer_reprimand_total = models.IntegerField(initial=0)
            # intercept_total = models.IntegerField(initial=0)

            if player.is_officer():
                officer_results = dict(
                    # bonus_total=group.officer_bonus_total,
                    # fine_total=group.civilian_fine_total,

                    # intercepts=group.intercept_total,

                    officer_base_pay=Constants.officer_start_balance,
                    fines=group.civilian_fine_total,
                    reprimands=group.officer_reprimand_total,
                    officer_reprimand_amount=Constants.officer_reprimand_amount,
                )

                round_results.update(officer_results)

            # send token count to group
            self.send(text_data=json.dumps({
                'round_results': round_results
            }))

    # Inform players that players have arrived so host can signal game start
    def sync_status(self, event):
        self.send(text_data=json.dumps({
            'sync_status': True,
        }))

    def round_info(self, event):
        self.send(text_data=json.dumps({
            'round_info': True,
        }))

    def round_active(self, event):
        self.send(text_data=json.dumps({
            'round_active': True,
        }))

    def round_timeout(self, event):
        self.send(text_data=json.dumps({
            'round_timeout': True,
        }))

    def round_end(self, event):
        self.send(text_data=json.dumps({
            'round_end': True,
        }))
