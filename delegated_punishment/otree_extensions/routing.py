from delegated_punishment.models import Player, Group
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
from django.urls import re_path
from django.conf.urls import url

from delegated_punishment.otree_extensions.game_consumer import GameConsumer
from delegated_punishment.otree_extensions.game_sync_consumer import GameSyncConsumer

websocket_routes = [
    # url(r'^delegated_punishment/sync/(?P<group_pk>[0-9]+)/', GameSyncConsumer),
    url(r'^delegated_punishment/(?P<group_pk>[0-9]+)/', GameConsumer),
]