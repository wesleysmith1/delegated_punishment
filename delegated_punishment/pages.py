from ._builtin import Page, WaitPage
import json, math
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from delegated_punishment.helpers import skip_period


class Game(Page):
    def is_displayed(self):
        if skip_period(self.session, self.round_number):
            return False
        return True

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
        vars_dict['balance_update_rate'] = self.session.config['balance_update_rate']
        vars_dict['defend_token_total'] = Constants.defend_token_total
        vars_dict['a_max'] = Constants.a_max
        vars_dict['beta'] = Constants.beta

        vars_dict['civilian_fine'] = Constants.civilian_fine_amount
        vars_dict['civilian_map_size'] = Constants.civilian_map_size
        vars_dict['defend_token_size'] = Constants.defend_token_size
        vars_dict['tutorial_duration'] = Constants.tutorial_duration
        vars_dict['officer_reprimand_amount'] = Constants.officer_reprimand_amount
        vars_dict['officer_review_probability'] = Constants.officer_review_probability
        vars_dict['steal_timeout_duration'] = Constants.steal_timeout_duration

        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)
            # for o in officer_tokens:
                # print("TOKEN {} - MAP  {} - X {:6.2f} - Y {:6.2f}".format(o.number, str(o.map), o.x, o.y)) #todo: these values are correct. Why are they not getting passed down to client?
            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

        if Constants.num_rounds > 1 and self.round_number == 1:
            timeout = True
        else:
            timeout = False

        vars_dict['timeout'] = timeout
        return vars_dict


class Wait(WaitPage):
    pass


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        if Constants.num_rounds > 1 and self.round_number < 3:
            # dont generate results for the tutorial and trial period
            pass
        else:
            self.group.generate_results()

            # only for periods 3-10
            if self.round_number > 2 or Constants.num_rounds == 1:
                for player in self.group.get_players():
                    player.participant.vars['balances'].append(math.floor(player.balance))


class ResultsPage(Page):
    timeout_seconds = 30
    timer_text = 'Time remaining on results page'

    def vars_for_template(self):
        vars_dict = dict()
        vars_dict['period'] = self.player.subsession.round_number
        vars_dict['steal_total'] = self.player.steal_total
        vars_dict['victim_total'] = self.player.victim_total
        vars_dict['balance'] = math.floor(self.player.balance)
        return vars_dict

    def is_displayed(self):
        if skip_period(self.session, self.round_number):
            return False

        if Constants.num_rounds == 1:
            return True
        elif self.round_number > 1:
            return True
        else:
            return False


class Intermission(Page):
    timeout_seconds = 80
    timer_text = 'Please wait for round to start'

    def is_displayed(self):
        if skip_period(self.session, self.round_number):
            return False

        if Constants.num_rounds > 1 and (self.round_number == 2 or self.round_number == 3 or self.round_number == 7):
            return True
        else:
            return False

    def vars_for_template(self):
        vars_dict = dict(
            steal_rate=Constants.civilian_steal_rate,
            fine=Constants.civilian_fine_amount,
            officer_bonus=self.group.get_player_by_id(1).participant.vars['officer_bonus'],
            officer_reprimand=Constants.officer_reprimand_amount
        )
        if self.round_number == 2:
            vars_dict['officer_bonus'] = self.session.config['tutorial_officer_bonus']
            info = 'We are about to perform a practice period to ensure everyone is familiar with the computer interface.'
        else:
            info = 'We are about to perform 4 periods sequentially.'
        vars_dict['info'] = info
        return vars_dict


class AfterTrialAdvancePage(Page):
    def is_displayed(self):
        if skip_period(self.session, self.round_number) or self.round_number == 2:
            return False

        return True


page_sequence = [Wait, Intermission, Game, ResultsWaitPage, ResultsPage, AfterTrialAdvancePage]
