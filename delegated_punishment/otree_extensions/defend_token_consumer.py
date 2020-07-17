from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from random import randrange
import numpy as np
from delegated_punishment.helpers import date_now_milli, DecimalEncoder

import logging
log = logging.getLogger(__name__)

from decimal import Decimal

from delegated_punishment.models import Player, Group, DefendToken, Constants, GameData, SurveyResponse, MechanismInput

class DefendTokenConsumer(WebsocketConsumer):

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
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        # print_padding = 25

        data_json = json.loads(text_data)

        print(data_json)

        group_id = data_json['group_id']
        player_id = data_json['player_id']
        player = Player.objects.get(pk=player_id)

        # print(f"groupid: {group_id} player_id {player_id}")

        survey_response = SurveyResponse.objects.get(player=player)
        print(survey_response)

        if data_json.get('survey'):

            survey_response.response = data_json['survey']
            survey_response.save()

        elif data_json.get('ogl'):
            """all 3 gl mechanisms"""

            updated_input = data_json['ogl']['data']

            MechanismInput.record(updated_input, player_id, group_id)

            print(updated_input)

            # append to a table or something.
            survey_response.total = updated_input
            survey_response.save()

            print('SURVEY RESPONSE UPDATED')

            survey_responses = SurveyResponse.objects.filter(group_id=group_id, participant=True)

            print(f"SURVEY RESPONSES {survey_responses.values_list('total', flat=True)}")

            costs, totals = SurveyResponse.calculate_ogl(survey_responses)
            #
            # log.info(f"value for player {player_id} is {costs[player_id]}")
            # # SurveyResponse.objects.filter(player_id=player_id).update(total=updated_input, mechanism_cost=responses[player_id])
            # for p_id in costs:
            #     p_cost = Decimal(costs[p_id])
            #     log.info(f"value for player {p_id} is {p_cost}")
            #     try:
            #         response = SurveyResponse.objects.filter(player_id=p_id)
            #         response.update(mechanism_cost=p_cost)
            #     except Exception:
            #         log.info(f"PLAYER {p_id} SPENT {p_cost} BUT WE COULD NOT UPDATE THE OBJECT")

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'ogl_update',
                    'provisional': {'totals': totals, 'costs': json.dumps(costs, cls=DecimalEncoder)}
                }
            )

    def ogl_update(self, event):
        provisional = event['provisional']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'provisional': provisional
        }))
