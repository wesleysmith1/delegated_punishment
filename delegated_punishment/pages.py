from ._builtin import Page, WaitPage
import json, math
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from json import JSONEncoder


class Game(Page):
    def vars_for_template(self):

        #  todo: we need to query player here since a blank model is being created instead
        #   of pulling from db. This is required to load data from the database.

        pjson = dict()
        pjson['player'] = self.player.pk
        pjson['map'] = self.player.map
        pjson['x'] = self.player.x
        pjson['y'] = self.player.y
        pjson['harvest_screen'] = self.player.harvest_screen

        vars_dict = dict()
        vars_dict['pjson'] = json.dumps(pjson)
        vars_dict['rand'] = str(random() * 1000)  # todo: remove
        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)
            # for o in officer_tokens:
                # print("TOKEN {} - MAP  {} - X {:6.2f} - Y {:6.2f}".format(o.number, str(o.map), o.x, o.y)) #todo: these values are correct. Why are they not getting passed down to client?
            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

        if Constants.num_rounds > 1 and self.round_number < 3:
            no_timeout = True
        else:
            no_timeout = False

        vars_dict['no_timeout'] = no_timeout
        return vars_dict


class Wait(WaitPage):
    pass


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # todo make sure that we are not doing this 5 times!
        if Constants.num_rounds > 1 and self.round_number > 2:
            # dont generate results for the tutorial and trial period
            pass
        else:
            self.group.generate_results()

            for player in self.group.get_players():
                player.participant.vars['balances'].append(math.floor(player.balance))


class ResultsPage(Page):
    timeout_seconds = 10
    timer_text = 'Time remaining on results page'

    def vars_for_template(self):
        vars_dict = dict()
        vars_dict['period'] = self.player.subsession.round_number
        vars_dict['steal_total'] = self.player.steal_total
        vars_dict['victim_total'] = self.player.victim_total
        vars_dict['balance'] = math.floor(self.player.balance)
        return vars_dict

    def is_displayed(self):
        if Constants.num_rounds == 1:
            return True
        elif self.round_number > 1:
            return True
        else:
            return False


class Intermission(Page):
    timeout_seconds = 120
    timer_text = 'Please wait for round to start'

    def is_displayed(self):
        if Constants.num_rounds > 1 and self.round_number == 3 or self.round_number == 7:
            return True
        else:
            return False

    def vars_for_template(self):
        vars_dict = dict(
            steal_rate=Constants.civilian_steal_rate,
            fine=Constants.civilian_fine_amount,
            officer_bonus=self.group.officer_bonus,
            officer_reprimand=Constants.officer_reprimand_amount
        )
        if self.round_number == 2:
            info = 'We are about to perform 4 periods sequentially'
        else:
            info = 'We are about to perform 4 periods sequentially.'
        vars_dict['info'] = info
        return vars_dict


class AutoAdvancePage(Page):
    """This page is for after the tutorial and the practice period so that
    the next periods are not started automatically"""
    def is_displayed(self):
        if self.round_number < 3:
            return True
        else:
            return False


page_sequence = [Wait, Intermission, Game, ResultsWaitPage, ResultsPage]
