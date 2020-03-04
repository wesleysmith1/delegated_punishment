from otree.api import Currency as c, currency_range

from ._builtin import Page, WaitPage
from .models import Constants
import csv
import random


class Introduction(Page):
    timeout_seconds = 20
    timer_text = 'Please wait to begin survey'


class SurveyWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # generate results here
        from survey.helpers import generate_payouts
        generate_payouts(self.group)


class FinalWaitPage(WaitPage):
    def after_all_players_arrive(self):
        from survey.helpers import generate_survey_csv
        generate_survey_csv(self.group)


class FinalPage(Page):
    pass


class MainSurvey(Page):
    form_model = 'player'
    form_fields = ['gender', 'race_ethnicity', 'strategy', 'feedback']


page_sequence = [SurveyWaitPage, Introduction, MainSurvey, FinalWaitPage, FinalPage]
