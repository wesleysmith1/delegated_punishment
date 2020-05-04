from ._builtin import Page, WaitPage
import json, math, csv
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from .models import Constants, DefendToken, Player, SurveyResponse
import random
from delegated_punishment.helpers import skip_period, write_session_dir, format_template_numbers, safe_list_sum
from delegated_punishment.models import Group

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
        # check to see if player was selected
        sr = SurveyResponse.objects.filter(group=self.group, player=self.player)

        if sr:
            selected = True
        else:
            selected = False

        template_vars = dict(
            timeout_seconds=Constants.dt_timeout_seconds,
            selected=selected,
            dt_method=Constants.dt_method,
            dt_range=Constants.dt_range,
            dt_payment_max=Constants.dt_payment_max,
            dt_q=Constants.dt_q,
            big_n=Constants.players_per_group-1,
            gamma=Constants.gamma,
            small_n=Constants.small_n
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

        # csv file output per player
        f = open(file_name, 'a', newline='')
        with f:
            writer = csv.writer(f)
            # write header

            if self.round_number == 1:
                writer.writerow(SurveyResponse.csv_header())

            # determine if players received 50 grain
            for r in survey_responses:
                row = r.csv_row()
                writer.writerow(row)

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
                    # import pdb
                    # pdb.set_trace()
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
                    results[i] = total * (Constants.players_per_group - 1) / count  # subtract officer
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
                    sr.mechanism_cost = sr.response[number_tokens]['total']
                    sr.save()

            log.info(f"number tokens for next round {number_tokens}")

            log.info(f"group updated")

            self.group.defend_token_total = int(number_tokens)
            self.group.defend_token_cost = safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True))
            self.group.save()
            # payments calculation
            self.group.calculate_survey_tax(survey_responses)

            log.info("defend tokens saved to group")
        elif Constants.dt_method == 1:
            # individual results calculated in consumer

            values = survey_responses.values_list('total', flat=True)
            token_total = sum(values)
            token_cost = safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True))
            log.info(f'number of tokens for period {self.group.round_number} is {token_total} from values: {values}')

            if token_total < 0:
                log.info(f'number of tokens is {token_total}. changing to 0')
                token_total = 0

            # Group.objects.filter(id=self.group.id).update(defend_token_total=token_total)
            self.group.defend_token_total = token_total
            self.group.defend_token_cost = token_cost
            self.group.save()

            # civilian payment
            self.group.calculate_ogl_tax(survey_responses)

        elif Constants.dt_method == 2:

            token_total = safe_list_sum(survey_responses.values_list('total', flat=True)) + Constants.dt_e0
            token_cost = safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True))

            Group.objects.filter(id=self.group.id).update(defend_token_total=token_total, defend_token_cost=token_cost)

            self.group.calculate_other_tax(survey_responses)

        elif Constants.dt_method == 3:

            token_total = safe_list_sum(survey_responses).values_list('total', flat=True) + Constants.dt_e0
            token_cost = safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True))

            Group.objects.filter(id=self.group.id).update(defend_token_total=token_total, defend_token_cost=token_cost)

            self.group.calculate_other_tax(survey_responses)

        else:
            log.error(f"RESULTS CANNOT BE GENERATED CORRECTLY FOR THIS METHOD {Constants.dt_method}")

        log.info(f"THERE ARE {self.group.defend_token_total} TOKENS FOR GROUP {self.group.id}")
        for i in range(self.group.defend_token_total):
            DefendToken.objects.create(number=i + 1, group=self.group,)

        log.info('Defend tokens created')


class DefendTokenInfo(Page):
    timeout_seconds = 60
    timer_text = 'The round will begin shortly'

    def vars_for_template(self):
        template_vars = dict(survey_payment=0, num_tokens=self.group.defend_token_total)

        try:
            survey_response = SurveyResponse.objects.get(player=self.player)
            your_tokens = survey_response.total

            cost = survey_response.tax
            participated = survey_response.participant

            if survey_response.valid:
                template_vars['survey_payment'] = Constants.rebate

        except SurveyResponse.DoesNotExist:
            log.error(f"survey response not found for player {self.player.id} for defendtokeninfo page")
            cost = 0
            your_tokens = 0
            participated = False

        template_vars['num_tokens'] = self.group.defend_token_total
        template_vars['token_cost'] = cost
        template_vars['total_token_cost'] = self.group.defend_token_cost

        template_vars['your_tokens'] = your_tokens
        template_vars['participated'] = participated

        return template_vars


class Wait(WaitPage):
    pass


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
            survey_response = SurveyResponse.objects.get(player=self.player)
            your_tokens = survey_response.total

            mechanism_cost = survey_response.mechanism_cost
            your_tax = survey_response.tax
            participated = survey_response.participant

            if survey_response.rebate is None:
                rebate = None #todo: this is super wrong
            else:
                rebate = survey_response.rebate

            if Constants.dt_method == 0:
                your_tokens = "Not applicable"

        except SurveyResponse.DoesNotExist:
            # this should only be for officer

            log.error(f"survey response not found for player {self.player.id} for defendtokeninfo page")
            mechanism_cost = None
            your_tax = 0
            your_tokens = "Not applicable"
            participated = False
            rebate = None

        # table variables
        vars_dict['rebate'] = rebate
        vars_dict['mechanism_cost'] = mechanism_cost
        vars_dict['your_tax'] = format_template_numbers(your_tax)
        vars_dict['your_tokens'] = your_tokens
        vars_dict['big_c'] = self.group.big_c
        vars_dict['participated'] = participated

        g = self.group.get_g() or None
        vars_dict['big_g'] = g

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
        vars_dict['defend_token_cost'] = format_template_numbers(self.group.defend_token_cost)
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

        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)

            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

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


class ResultsPage(Page):
    timeout_seconds = 300000
    timer_text = 'Time remaining on results page'

    def vars_for_template(self):
        vars_dict = dict()

        try:
            sr = SurveyResponse.objects.get(player=self.player)
        except SurveyResponse.DoesNotExist:

            if self.player.id_in_group != 1:
                log.error(f"could not find survey result for player {self.player.id}")

            rebate = None
            mechanism_cost = None
            your_tax = None

            balance = before_tax = math.floor(self.player.balance)
            tax = 0
            your_tokens = "Not applicable"
            participated = False

        else:
            if sr.rebate is None:
                rebate = None #todo: this is super wrong
            else:
                rebate = sr.rebate

            if Constants.dt_method == 0:
                your_tokens = "Not applicable"
            else:
                your_tokens = sr.total

            mechanism_cost = sr.mechanism_cost
            your_tax = sr.tax

            balance = math.floor(self.player.balance)
            before_tax = math.floor(self.player.balance + sr.tax)
            tax = math.floor(sr.tax)
            participated = sr.participant

        # table variables
        vars_dict['rebate'] = rebate
        vars_dict['mechanism_cost'] = mechanism_cost
        vars_dict['your_tax'] = format_template_numbers(your_tax)
        vars_dict['your_tokens'] = your_tokens
        vars_dict['big_c'] = self.group.big_c
        vars_dict['participated'] = participated

        g = self.group.get_g()
        vars_dict['big_g'] = g

        vars_dict['before_tax'] = format_template_numbers(before_tax)
        vars_dict['tax'] = format_template_numbers(tax)
        vars_dict['balance'] = format_template_numbers(balance)

        vars_dict['defend_token_cost'] = format_template_numbers(self.group.defend_token_cost) #todo: make sure we want to save percise value
        vars_dict['defend_token_total'] = self.group.defend_token_total
        vars_dict['your_tokens'] = your_tokens
        vars_dict['participated'] = participated

        # summary variables
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
            return True


class AfterTrialAdvancePage(Page):
    def is_displayed(self):
        if skip_period(self.session, self.round_number) or self.round_number == 2:
            return False

        return True


page_sequence = [SurveyInit, Intermission, DefendTokenSurvey, DefendTokenWaitPage, Wait, Game, ResultsWaitPage, ResultsPage, AfterTrialAdvancePage]
