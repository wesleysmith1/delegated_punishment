from ._builtin import Page, WaitPage
import json, math
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from delegated_punishment.helpers import skip_round


class Game(Page):
    # the template can be changed to GameTest.html to. Each tab sends up test data at intervals to the backend
    # template_name = 'delegated_punishment/GameTest.html'
    template_name = 'delegated_punishment/Game.html'

    def is_displayed(self):
        if skip_round(self.session, self.round_number):
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

        vars_dict['tutorial'] = Constants.num_rounds > 1 and self.round_number == 1

        # if the input is zero there is no delay after advance slowest is selected.
        if self.round_number == 1:
            vars_dict['advance_delay_milli'] = Constants.results_modal_seconds * 1000
        else:
            vars_dict['advance_delay_milli'] = 0

        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)
            # for o in officer_tokens:
            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

        config = dict(
            balance_update_rate=self.session.config['balance_update_rate'],
            defend_token_total=Constants.defend_token_total,
            a_max=Constants.a_max,
            beta=Constants.beta,
            civilian_fine=Constants.civilian_fine_amount,
            civilian_map_size=Constants.civilian_map_size,
            defend_token_size=Constants.defend_token_size,
            tutorial_duration_seconds=Constants.tutorial_duration_seconds,
            officer_reprimand_amount=Constants.officer_reprimand_amount,
            officer_review_probability=Constants.officer_review_probability,
            steal_timeout_milli=Constants.steal_timeout_milli,
            game_duration_seconds=Constants.game_duration_seconds,
            players_per_group=Constants.players_per_group,
            civilians_per_group=Constants.civilians_per_group,
            steal_token_slots=Constants.steal_token_slots,
            results_modal_seconds=Constants.results_modal_seconds,
        )

        vars_dict['config'] = json.dumps(config)

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


class Intermission(Page):
    timeout_seconds = 80
    timer_text = 'Please wait for round to start'

    def is_displayed(self):
        if skip_round(self.session, self.round_number):
            return False

        if Constants.num_rounds > 1 and (self.round_number == 2 or self.round_number == 3 or self.round_number == 7):
            return True
        else:
            return False

    def vars_for_template(self):
        vars_dict = dict(
            civilian_incomes=Constants.civilian_incomes_low,
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
        if skip_round(self.session, self.round_number) or self.round_number == 2:
            return True

        return False


page_sequence = [Wait, Intermission, Game, ResultsWaitPage, AfterTrialAdvancePage]
