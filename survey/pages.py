from otree.api import Currency as c, currency_range

from ._builtin import Page, WaitPage
from .models import Constants
import csv
import random

class NameSurvey(Page):
    form_model = 'player'
    form_fields = ['name']


class SurveyWaitPage(WaitPage):
    def after_all_players_arrive(self):
        print('ALL PLAYERS HAVE ARRIVED SUCKA {}'.format(self.group.id))
        # generate results here
        from survey.helpers import generate_payouts
        generate_payouts(self.group)



class MainSurvey(Page):
    form_model = 'player'
    form_fields = ['gender', 'race_ethnicity', 'confused', 'confused_explanation', 'strategy', 'feedback']


page_sequence = [NameSurvey, SurveyWaitPage, MainSurvey]
