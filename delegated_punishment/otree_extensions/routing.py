from delegated_punishment.models import Player, Group
from otree.models import Participant
from otree.models_concrete import ParticipantToPlayerLookup
from django.urls import re_path
from django.conf.urls import url

from .consumers import GameConsumer

# todo: is the a different channel for each group
websocket_routes = [
    url(r'^delegated_punishment/(?P<player_pk>[0-9]+)/(?P<group_pk>[0-9]+)/', GameConsumer),
]   