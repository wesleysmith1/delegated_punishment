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
        # generate results here
        from survey.helpers import generate_payouts
        generate_payouts(self.group)


class FinalPage(Page):
    pass


class MainSurvey(Page):
    form_model = 'player'
    form_fields = ['gender', 'race_ethnicity', 'strategy', 'feedback']


page_sequence = [NameSurvey, SurveyWaitPage, MainSurvey, FinalPage]
