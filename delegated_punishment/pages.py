from ._builtin import Page, WaitPage
import json, math
import operator

from .models import Constants, DefendToken, Player, Group, GameStatus
from delegated_punishment.helpers import skip_round
from delegated_punishment.income_distributions import IncomeDistributions

import logging
log = logging.getLogger(__name__)


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

        # group object must be retrieved otherwise it is not updated with recent values
        group = Group.objects.get(id=self.group.id)

        # (bugfix) get player object to make sure that they are not stealing
        player = Player.objects.get(id=self.player.id)
        player.stop_stealing()

        # log.info(f'loading template var for player {self.player.id}. group game status {group.game_status}')

        # income configuration number
        config_key = self.session.config['civilian_income_config']

        civilian_ids = [x + Constants.players_per_group - Constants.civilians_per_group for x in
               range(1, Constants.players_per_group + 1)]

        # todo: if tutorial or practice we need different variables
        if self.round_number < 3:  # tutorial or practice round
            tut_civ_income = self.session.config['tutorial_civilian_income']
            tut_o_bonus = self.session.config['tutorial_officer_bonus']

            incomes = [tut_civ_income] * Constants.civilians_per_group
            incomes_dict = dict(zip(civilian_ids, incomes))
            incomes_dict = dict(sorted(incomes_dict.items(), key=operator.itemgetter(1)))

            start_modal_object = dict(
                civilian_incomes=incomes_dict,
                steal_rate=Constants.civilian_steal_rate,
                civilian_fine=Constants.civilian_fine_amount,
                officer_bonus=tut_o_bonus,
                officer_reprimand=self.group.officer_reprimand_amount,
            )
        else:
            incomes = IncomeDistributions.get_group_income_distribution(config_key, self.round_number)
            incomes_dict = dict(zip(civilian_ids, incomes))
            sorted(incomes_dict.values()) #todo: this is not working here

            start_modal_object = dict(
                civilian_incomes=incomes_dict,
                steal_rate=Constants.civilian_steal_rate,
                civilian_fine=Constants.civilian_fine_amount,
                officer_bonus=self.group.get_player_by_id(1).participant.vars['officer_bonus'],
                officer_reprimand=self.group.officer_reprimand_amount,
            )

        config = dict(
            balance_update_rate=self.session.config['balance_update_rate'],
            defend_token_total=Constants.defend_token_total,
            a_max=Constants.a_max,
            beta=Constants.beta,
            civilian_fine=Constants.civilian_fine_amount,
            civilian_map_size=Constants.civilian_map_size,
            defend_token_size=Constants.defend_token_size,
            tutorial_duration_seconds=Constants.tutorial_duration_seconds,
            officer_reprimand_amount=self.group.officer_reprimand_amount,
            steal_pause_duration=Constants.steal_pause_duration,
            defend_pause_duration=Constants.defend_pause_duration,
            officer_review_probability=Constants.officer_review_probability,
            steal_timeout_milli=Constants.steal_timeout_milli,
            game_duration_seconds=Constants.game_duration_seconds,
            players_per_group=Constants.players_per_group,
            civilians_per_group=Constants.civilians_per_group,
            steal_token_slots=Constants.steal_token_slots,
            start_modal_seconds=Constants.start_modal_seconds,
            start_modal_object=start_modal_object,
            results_modal_seconds=Constants.results_modal_seconds,
            game_status=group.game_status,
        )

        vars_dict['config'] = json.dumps(config)

        return vars_dict


class Wait(WaitPage):
    pass


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        if Constants.num_rounds > 1 and self.round_number < 3:
            # dont generate results for the tutorial and trial round
            pass
        else:
            # only for round 3-10
            if self.round_number > 2 or Constants.num_rounds == 1:
                for player in self.group.get_players():
                    player.participant.vars['balances'].append(math.floor(player.balance))
            # csv data added for rounds 
            self.group.generate_results()



class Intermission(Page):
    timeout_seconds = 80
    timer_text = 'Please wait for round to start'

    def is_displayed(self):
        if skip_round(self.session, self.round_number):
            return False

        if Constants.num_rounds > 1 and (self.round_number == 2 or self.round_number == 3 or self.round_number == 8):
            return True
        else:
            return False

    def vars_for_template(self):

        config_key = self.session.config['civilian_income_config']
        group_incomes = IncomeDistributions.get_group_income_distribution(config_key, self.round_number)

        # todo: if tutorial or practice we need different variables
        if self.round_number < 3:  # tutorial or practice round

            tut_civ_income = self.session.config['tutorial_civilian_income']
            tut_o_bonus = self.session.config['tutorial_officer_bonus']

            vars_dict = dict(
                civilian_incomes=[tut_civ_income] * Constants.civilians_per_group,
                # harvest_income=player.income,
                steal_rate=Constants.civilian_steal_rate,
                civilian_fine=Constants.civilian_fine_amount,
                officer_bonus=tut_o_bonus,
                officer_reprimand=self.group.officer_reprimand_amount,
            )
        else:
            vars_dict = dict(
                civilian_incomes=group_incomes,
                # harvest_income=player.income,
                steal_rate=Constants.civilian_steal_rate,
                civilian_fine=Constants.civilian_fine_amount,
                officer_bonus=self.group.get_player_by_id(1).participant.vars['officer_bonus'],
                officer_reprimand=self.group.officer_reprimand_amount,
            )

        # vars_dict = dict(
        #     civilian_incomes=round_incomes,
        #     steal_rate=Constants.civilian_steal_rate,
        #     fine=Constants.civilian_fine_amount,
        #     officer_bonus=self.group.get_player_by_id(1).participant.vars['officer_bonus'],
        #     officer_reprimand=self.group.officer_reprimand_amount
        # )
        if self.round_number == 2:
            vars_dict['officer_bonus'] = self.session.config['tutorial_officer_bonus']
            info = 'We are about to perform a practice round to ensure everyone is familiar with the computer interface.'
        else:
            info = 'We are about to perform 5 rounds sequentially.'
        vars_dict['info'] = info
        vars_dict['officer_review_probability'] = Constants.officer_review_probability*100
        return vars_dict


class AfterTrialAdvancePage(Page):
    def is_displayed(self):
        if skip_round(self.session, self.round_number) or self.round_number == 2 or self.round_number == 7:
            return True

        return False


page_sequence = [Wait, Intermission, Game, ResultsWaitPage, AfterTrialAdvancePage]
