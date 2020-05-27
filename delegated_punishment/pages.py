from ._builtin import Page, WaitPage
import json, math, csv
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from .models import Constants, DefendToken, Player, SurveyResponse
import random
from delegated_punishment.helpers import skip_period, write_session_dir, format_template_numbers, safe_list_sum
from delegated_punishment.models import Group
from delegated_punishment.mechanism import MechCSVBuilder

from decimal import Decimal

import logging
log = logging.getLogger(__name__)


class SurveyInit(WaitPage):
    def after_all_players_arrive(self):
        selected_players = Player.objects.filter(group_id=self.group.pk).exclude(id_in_group=1)

        sample_size = Constants.small_n

        if Constants.dt_method == 0:
            selected_players = random.sample(list(selected_players), sample_size)
        elif Constants.dt_method == 1:
            selected_players = selected_players
        elif Constants.dt_method == 2:
            selected_players = random.sample(list(selected_players), sample_size)
        elif Constants.dt_method == 3:
            selected_players = random.sample(list(selected_players), sample_size)

        for p in selected_players:
            SurveyResponse.objects.create(group=self.group, player=p, response=dict(), participant=True)


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


class DefendTokenSurvey(Page):

    def vars_for_template(self):
        selected = False

        try:
            sr = SurveyResponse.objects.get(group=self.group, player=self.player)
        except SurveyResponse.DoesNotExist:
            pass
        else:
            selected = True

        template_vars = dict(
            timeout_seconds=Constants.dt_mechanism_seconds,
            selected=selected,
            dt_method=Constants.dt_method,
            dt_range=Constants.dt_range,
            dt_payment_max=Constants.dt_payment_max,
            dt_q=Constants.dt_q,
            big_n=Constants.players_per_group-1,
            gamma=Constants.gamma,
            omega=Constants.omega,
            small_n=Constants.small_n,
        )

        return template_vars


class DefendTokenWaitPage(WaitPage):

    def after_all_players_arrive(self):
        """calculate how many defend tokens are going to be used"""

        survey_responses = SurveyResponse.objects.filter(group=self.group)
        print("THAT WAS THE SURVEY RESULTS")
        print(survey_responses)

        file_path = write_session_dir(self.session.config['session_identifier'])
        file_name = f"{file_path}Session_{self.group.session_id}_Group_{self.group.id}_{self.session.vars['session_date']}_{self.session.vars['session_start']}.csv"

        MechCSVBuilder(Constants.dt_method, survey_responses, file_name, input_range=Constants.dt_range)

        # method specific code
        if Constants.dt_method == 0:

            results = dict()
            for i in range(1, Constants.dt_range + 1):
                count = 0
                total = 0

                token_index = str(i)

                for r in survey_responses:
                    print('HERE IS A SURVEY RESULT')
                    print(r)

                    if r.response.get(token_index):
                        if r.response[token_index].get('wtp'):
                            log.info(f"HERE IT IS THE RESPONSE FOR THIS PLAYER IS {r.response[token_index]['wtp']}")

                            try:
                                response = r.response[token_index]['wtp']

                                if response is not 'null':
                                    count += 1
                                    total += response
                            except:
                                log.info(f"COULD NOT INCREMENT TOTAL. TOTAL IS CURRENTLY AT {total}. Here was the value of response: {response}")

                            log.error(f'ROW {i}, RESPONSE {response} COUNT {count} TOTAL {total}')
                        pass
                    else:
                        print("THERE WAS AN ERROR COLLECTING DATA FROM RESPONSE BELOW...")
                        print(r.response)
                try:
                    results[i] = total * Constants.big_n / count
                except ZeroDivisionError:
                    # there were no responses
                    results[i] = 0

            log.info('survey results generated')

            number_tokens = 0
            for i in range(Constants.dt_range, 0, -1):
                print(f"token count {i}, average {results[i]}")
                if results[i] >= Constants.dt_q:
                    number_tokens = i
                    break

            for sr in survey_responses:
                if sr.response.get(number_tokens):
                    sr.mechanism_cost = Decimal(sr.response[number_tokens]['total'])
                    sr.save()

            log.info(f"number tokens for next round {number_tokens}")

            log.info(f"group updated")

            self.group.defend_token_total = int(number_tokens)
            self.group.defend_token_cost = Decimal(safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True)))
            self.group.save()
            # payments calculation
            self.group.calculate_survey_tax(survey_responses)

            log.info("defend tokens saved to group")
        elif Constants.dt_method == 1:
            # individual results calculated in consumer

            values = survey_responses.values_list('total', flat=True)
            token_total = sum(values)
            token_cost = Decimal(safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True)))
            log.info(f'number of tokens for period {self.group.round_number} is {token_total} from values: {values}')

            if token_total < 0:
                log.info(f'number of tokens is {token_total}. changing to 0')
                token_total = 0

            # Group.objectsm.filter(id=self.group.id).update(defend_token_total=token_total)
            self.group.defend_token_total = token_total
            self.group.defend_token_cost = token_cost
            self.group.save()

            # civilian payment
            self.group.calculate_ogl_tax(survey_responses)

        elif Constants.dt_method == 2:

            token_total = safe_list_sum(survey_responses.values_list('total', flat=True)) + Constants.dt_e0

            if token_total < 0:
                log.info(f'number of tokens is {token_total}. changing to 0')
                token_total = 0

            token_cost = Decimal(safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True)))

            self.group.defend_token_total = token_total
            self.group.defend_token_cost = token_cost
            self.group.save()

            self.group.calculate_other_tax(survey_responses)

        elif Constants.dt_method == 3:

            token_total = safe_list_sum(survey_responses.values_list('total', flat=True)) + Constants.dt_e0

            if token_total < 0:
                log.info(f'number of tokens is {token_total}. changing to 0')
                token_total = 0

            token_cost = Decimal(safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True)))

            self.group.defend_token_total = token_total
            self.group.defend_token_cost = token_cost
            self.group.save()

            Group.objects.filter(id=self.group.id).update(defend_token_total=token_total, defend_token_cost=token_cost)

            self.group.calculate_other_tax(survey_responses)

        else:
            log.error(f"RESULTS CANNOT BE GENERATED CORRECTLY FOR THIS METHOD {Constants.dt_method}")

        log.info(f"THERE ARE {self.group.defend_token_total} TOKENS FOR GROUP {self.group.id}")
        for i in range(self.group.defend_token_total):
            DefendToken.objects.create(number=i + 1, group=self.group,)

        log.info('Defend tokens created')


class Wait(WaitPage):
    pass

class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DecimalEncoder, self)._iterencode(o, markers)

class Game(Page):
    # the template can be changed to GameTest.html to. Each tab sends up test data at intervals to the backend
    # template_name = 'delegated_punishment/GameTest.html'
    template_name = 'delegated_punishment/Game.html'

    def is_displayed(self):
        if skip_period(self.session, self.round_number):
            return False
        return True

    def vars_for_template(self):
        #  todo: we need to query player here since a blank model is being created instead
        #   of pulling from db. This is required to load data from the database.

        vars_dict = dict(survey_payment=0, num_tokens=self.group.defend_token_total)

        try:
            response = SurveyResponse.objects.get(player=self.player)
            # your_tokens = response.total

            # your_tax = response.tax

            # if Constants.dt_method == 0:
                # your_tokens = None

        except SurveyResponse.DoesNotExist:
            # this should only be for officer

            log.error(f"survey response not found for player {self.player.id} for defendtokeninfo page")
            # your_tax = None
            # your_tokens = None

            response = None
        finally:
            start_object = self.group.generate_start_vars(self.player.id_in_group, response)

        vars_dict['start_object'] = start_object

        # game variables
        pjson = dict()
        pjson['player'] = self.player.pk
        pjson['map'] = self.player.map
        pjson['x'] = self.player.x
        pjson['y'] = self.player.y
        pjson['harvest_screen'] = self.player.harvest_screen

        vars_dict['pjson'] = json.dumps(pjson)
        vars_dict['balance_update_rate'] = self.session.config['balance_update_rate']
        vars_dict['defend_token_total'] = self.group.defend_token_total
        vars_dict['a_max'] = Constants.a_max
        vars_dict['beta'] = Constants.beta

        vars_dict['civilian_fine'] = Constants.civilian_fine_amount
        vars_dict['civilian_map_size'] = Constants.civilian_map_size
        vars_dict['defend_token_size'] = Constants.defend_token_size
        vars_dict['tutorial_duration_seconds'] = Constants.tutorial_duration_seconds
        vars_dict['officer_reprimand_amount'] = Constants.officer_reprimand_amount
        vars_dict['officer_review_probability'] = Constants.officer_review_probability
        vars_dict['steal_timeout_duration'] = Constants.steal_timeout_duration
        vars_dict['game_duration_seconds'] = Constants.game_duration_seconds
        vars_dict['players_per_group'] = Constants.players_per_group
        vars_dict['steal_token_positions'] = Constants.steal_token_positions

        vars_dict['results_modal_seconds'] = Constants.results_modal_seconds
        vars_dict['start_modal_seconds'] = Constants.start_modal_seconds

        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)

            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results, cls=DecimalEncoder)

        if Constants.num_rounds > 1 and self.round_number == 1:
            timeout = True
        else:
            timeout = False

        vars_dict['timeout'] = timeout

        # this variable determines if game was started
        # i.e. the game started then a player refreshed their page.
        vars_dict['game_started'] = self.group.game_start and self.group.game_start > 0

        return vars_dict


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # recalculate taxes and update player balances
        self.group.apply_taxes()

        if Constants.num_rounds > 1 and self.round_number < 3:
            # dont generate results for the tutorial and trial period
            pass
        else:
            self.group.generate_results()

            # only for periods 3-10
            if self.round_number > 2 or Constants.num_rounds == 1:
                for player in self.group.get_players():
                    player.participant.vars['balances'].append(math.floor(player.balance))


class AfterTrialAdvancePage(Page):
    def is_displayed(self):
        if skip_period(self.session, self.round_number) or self.round_number == 2:
            return False

        return True


page_sequence = [SurveyInit, Intermission, DefendTokenSurvey, DefendTokenWaitPage, Wait, Game, ResultsWaitPage, AfterTrialAdvancePage]
