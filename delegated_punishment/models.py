import datetime

from django.contrib.postgres.fields import JSONField
from django.db import transaction
from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)
from otree.db.models import Model, ForeignKey
from random import randrange
import math

from delegated_punishment.helpers import safe_list_sum, format_template_numbers
from delegated_punishment.mechanism import OglMechanism, OtherMechanism, SurveyMechanism

import logging
log = logging.getLogger(__name__)

doc = """
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment'
    players_per_group = 9
    num_rounds = 10
    # num_rounds = 1  # testing purposes

    # officer_intersection_payout = 10  # b: how much officer makes for intersection

    epoch = datetime.datetime.utcfromtimestamp(0)

    civilian_start_balance = 0

    # these variables will be subject to change the most
    civilian_fine_amount = 120
    civilian_steal_rate = 13  # S: amount of grain stolen per second (CONSTANT ACROSS GROUPS AND PERIODS)

    officer_review_probability = .33  # THETA: chance that an intersection result will be reviewed
    officer_reprimand_amount = 600  # P punishment for officer if innocent civilian is punished

    civilian_incomes_low = [38, 39, 40, 41, 43, 99, 99, 99]  # todo: add correct balances here
    civilian_incomes_high = [57, 41, 38, 34, 31, 99, 99, 99]
    # officer_incomes = [0, 10, 20]
    officer_incomes = [180, 180, 180]
    # officer_incomes = [0, 180, 600]


    # also change in officer.css
    defend_token_size = 68  # this is the size of the tokens that players with role of officer drag around
    civilian_map_size = 200

    beta = .9
    a_max = 6

    tutorial_duration_seconds = 5  # 1800
    game_duration_seconds = 5  # 198
    results_modal_seconds = 9000  # 30
    start_modal_seconds = 10

    officer_start_balance = 1000

    steal_timeout_duration = 200000

    steal_token_positions = 20

    small_n = 4
    dt_method = 0
    dt_q = 10
    dt_timeout_seconds = 120  # seconds
    previous_modal_mili = 10000  # miliseconds

    dt_e0 = 5
    dt_range = 10
    dt_payment_max = 10
    big_n = 8
    gamma = 30
    rebate = 0


class Subsession(BaseSubsession):

    def creating_session(self):
        """This is called once for each round"""

        # set session start time
        from delegated_punishment.helpers import date_now_milli
        session_start = date_now_milli()
        self.session.vars['session_start'] = session_start
        self.session.vars['session_date'] = datetime.datetime.today().strftime('%Y%m%d')

        groups = self.get_groups()

        # this code is the terrible way that officer income is determined for session
        if self.round_number == 1:
            index = 0
            for gr in groups:
                officer_bonus = Constants.officer_incomes[index]
                officer = gr.get_player_by_id(1)
                officer.income = officer_bonus
                officer_participant = officer.participant
                officer_participant.vars['officer_bonus'] = officer_bonus

                # save group id
                officer_participant.vars['group_id'] = index+1

                # officer_participant.save()
                index += 1

                for p in gr.get_players():
                    if p.id_in_group > 1:
                        p.income = self.session.config['tutorial_civilian_income']
                        p.save()

        for g in groups:
            for p in g.get_players():
                # initialize balances list
                p.participant.vars['balances'] = []
                p.participant.vars['steal_start'] = p.steal_start

                if p.is_officer():
                    p.balance = Constants.officer_start_balance

                # demo session does not need further configuration
                if Constants.num_rounds != 1:

                    # check if round is tutorial or trial period
                    if self.round_number < 3:
                        if p.id_in_group > 1:
                            p.income = self.session.config['tutorial_civilian_income']
                        else:
                            p.income = self.session.config['tutorial_officer_bonus']
                    else:
                        # set harvest amount for civilians
                        if p.id_in_group > 1:
                            incomes = Constants.civilian_incomes_low if self.round_number < 7 \
                                else Constants.civilian_incomes_high
                            i = incomes[p.id_in_group-2]
                            p.income = i
                        else:
                            # is officer
                            p.income = p.participant.vars['officer_bonus']

                else:
                    # only one round being played
                    officer = g.get_player_by_id(1)
                    officer.income = self.session.config['tutorial_officer_bonus']


class Group(BaseGroup):
    game_start = models.FloatField(blank=True)
    officer_bonus = models.IntegerField(initial=0)
    players_ready = models.IntegerField(initial=0)
    defend_token_total = models.IntegerField(initial=0)
    defend_token_cost = models.FloatField(initial=0)
    officer_bonus_total = models.IntegerField(initial=0)
    civilian_fine_total = models.IntegerField(initial=0)
    big_c = models.FloatField(blank=True, default=None)

    # todo: turn this into a proper factory or part of a generator. :)
    @classmethod
    def round_outcome_variables(cls, group, player):

        try:
            response = SurveyResponse.objects.get(player=player)
        except SurveyResponse.DoesNotExist:
            response = None

        if Constants.dt_method == 0:
            vars = SurveyMechanism.result_vars(group, player, response)
        elif Constants.dt_method == 1:
            vars = OglMechanism.result_vars(group, player, response)
        elif Constants.dt_method > 1:
            vars = OtherMechanism.result_vars(group, player, response)
        else:
            # todo: there was an error:
            pass

        return vars
        # try:
        #     sr = SurveyResponse.objects.get(player=player)
        # except SurveyResponse.DoesNotExist:
        #
        #     if player.id_in_group != 1:
        #         log.error(f"could not find survey result for player {player.id}")
        #
        #     rebate = None
        #     mechanism_cost = None
        #     your_tax = None
        #
        #     balance = before_tax = math.floor(player.balance)
        #     tax = 0
        #     your_tokens = None
        #
        # else:
        #     if sr.rebate is None:
        #         rebate = None  # todo: this is super wrong
        #     else:
        #         rebate = sr.rebate
        #
        #     if Constants.dt_method == 0:
        #         your_tokens = None
        #     else:
        #         your_tokens = sr.total
        #
        #     mechanism_cost = sr.mechanism_cost
        #     your_tax = format_template_numbers(sr.tax)
        #
        #     before_tax = math.floor(player.balance)
        #     # tax = math.floor(sr.tax)
        #
        #     #todo: tax has not been applied yet. is there a way to make this more clear?
        #     balance = math.floor(player.balance - sr.tax)
        #
        # # table variables
        # vars_dict['rebate'] = rebate
        # vars_dict['mechanism_cost'] = mechanism_cost
        # vars_dict['your_tax'] = your_tax
        # vars_dict['your_tokens'] = your_tokens
        # vars_dict['big_c'] = group.big_c
        #
        # g = group.get_g()
        # vars_dict['big_g'] = g
        #
        # vars_dict['before_tax'] = format_template_numbers(before_tax)
        # # vars_dict['tax'] = format_template_numbers(tax)
        # vars_dict['balance'] = format_template_numbers(balance)
        #
        # vars_dict['defend_token_cost'] = format_template_numbers(
        #     group.defend_token_cost)  # todo: make sure we want to save percise value
        # vars_dict['defend_token_total'] = group.defend_token_total
        # vars_dict['your_tokens'] = your_tokens
        #
        # # summary variables
        # vars_dict['period'] = player.subsession.round_number
        # vars_dict['steal_total'] = player.steal_total
        # vars_dict['victim_total'] = player.victim_total
        # return vars_dict

    @classmethod
    def intersection_update(cls, group_id, bonus, fine):
        with transaction.atomic():
            me = Group.objects.select_for_update().get(id=group_id)
            me.officer_bonus_total += bonus
            me.civilian_fine_total += fine
            me.save()

    def check_game_status(self, time):
        if self.group_ready():
            event_time = time
            if self.game_start:
                return Constants.game_duration_seconds*1000 - (time - self.game_start)
            else:
                game_data_dict = {
                    'event_time': event_time,
                    'event_type': 'period_start'
                }
                GameData.objects.create(
                    event_time=event_time,
                    p=self.get_players()[0].pk,
                    g=self.id,
                    s=self.session.id,
                    round_number=self.round_number,
                    jdata=game_data_dict
                )
                return Constants.game_duration_seconds
        return False

    def generate_start_vars(self, id_in_group, response=None):

        if Constants.dt_method == 0:

            x = SurveyMechanism.start_vars(
                id_in_group,
                self.defend_token_total,
                self.defend_token_cost,
                response,
            )

        elif Constants.dt_method == 1:

            x = OglMechanism.start_vars(
                id_in_group,
                self.defend_token_total,
                self.defend_token_cost,
                response,
            )

        elif Constants.dt_method > 1:

            x = OtherMechanism.start_vars(
                id_in_group,
                self.defend_token_total,
                self.defend_token_cost,
                response,
            )

        else:
            x = None

        return x


    def group_ready(self):
        """Have all player pages loaded"""
        if self.players_ready == Constants.players_per_group:
            return True
        return False

    def balance_update(self, time):
        players = self.get_players()
        # players = Player.objects.filter(group_id=self.id).values_list('map', 'last_updated', 'balance', 'roi', 'id_in_group', 'victim_count', 'steal_count')

        balance_update = dict()

        # maps being stolen from
        active_maps = {}

        for i in range(1, Constants.players_per_group+1):
            active_maps[i] = 0

        for player in players:
            if player.map > 0:
                active_maps[player.map] += 1

            balance_update[player.id_in_group] = dict(
                balance=player.get_balance(time),
                map=player.map,
                victim_count=player.victim_count,
                steal_count=player.steal_count,
            )
            balance_update['active_maps'] = active_maps

        return balance_update

    def generate_results(self):
        players = self.get_players()

        # Initial civilian steal locations for csv
        player_ids_in_session = []
        steal_starts = []
        for p in players:
            steal_starts.append(p.participant.vars['steal_start'])
            player_ids_in_session.append(p.participant.id_in_session)

        officer_participant = self.get_player_by_id(1).participant
        officer_bonus = officer_participant.vars['officer_bonus']
        group_id = officer_participant.vars['group_id']

        if self.session.config['low_to_high']:
            if self.subsession.round_number < 7:
                income_distribution = Constants.civilian_incomes_low
            else:
                income_distribution = Constants.civilian_incomes_high
        else:
            if self.subsession.round_number < 7:
                income_distribution = Constants.civilian_incomes_high
            else:
                income_distribution = Constants.civilian_incomes_low

        meta_data = dict(
            round_number=self.subsession.round_number,
            session_id=self.subsession.session_id,
            steal_starts=steal_starts,
            session_start=self.session.vars['session_start'],
            session_date=self.session.vars['session_date'],
            group_pk=self.pk,
            group_id=group_id,
            officer_bonus=officer_bonus,
            income_distribution=income_distribution,
            player_ids_in_session=player_ids_in_session
        )

        # todo: this is here to prevent import error because Constants cannot be loaded.
        from delegated_punishment.generate_data import generate_csv
        generate_csv(self.session, self.subsession, meta_data)

    def get_set_c(self, sum_costs=None):

        if not sum_costs:
            sum_costs = safe_list_sum(SurveyResponse.objects.filter(group=self).values_list('mechanism_cost', flat=True))

        # TODO:
        # rebate * small_n will change if rebates require some form of validaiton.
        c = self.defend_token_total * Constants.dt_q + (Constants.rebate * Constants.small_n) - sum_costs
        log.info(f"cost for group {self.id} in round {self.round_number} : {sum_costs}, c: {c}, token_count: {self.defend_token_total}")

        self.big_c = c
        self.save()
        log.info(f"THIS IS THE BIG C VALUE {self.big_c}")

        return c

    def get_g(self):
        """return net costs of policy"""
        bonus_amount = self.get_player_by_id(1).income
        g = self.officer_bonus_total * bonus_amount - self.civilian_fine_total * Constants.civilian_fine_amount
        return g

    def calculate_survey_tax(self, survey_responses=None):

        if not survey_responses:
            survey_responses = SurveyResponse.objects.filter(group_id=self.id)

        # filter out empty values
        sum_costs = safe_list_sum(survey_responses.values_list('mechanism_cost', flat=True))
        c = self.defend_token_total * Constants.dt_q
        g = self.get_g()

        all_participants_fee = (c + g) / Constants.big_n

        self.defend_token_cost = all_participants_fee * Constants.big_n

        for player in self.get_players():

            if player.id_in_group == 1:
                continue

            try:
                sr = survey_responses.get(player_id=player.id)
                sr.mechanism_cost = all_participants_fee
                sr.tax = all_participants_fee
            except SurveyResponse.DoesNotExist:
                log.error(f"player {player.id} did not participate in survey in round: {self.round_number}")
                SurveyResponse.objects.create(player=player, group=self, mechanism_cost=None, tax=all_participants_fee, participant=False)
            else:
                sr.save()

    def calculate_ogl_tax(self, survey_responses=None):
        """ogl actually has no tax but we subtract the rebate"""

        if not survey_responses:
            survey_responses = SurveyResponse.objects.filter(group_id=self.id)

        g = self.get_g()
        self.get_set_c()
        remaining_cost = g / Constants.big_n

        for player in self.get_players():
            if player.id_in_group == 1:
                continue

            try:
                sr = survey_responses.get(player_id=player.id)
            except SurveyResponse.DoesNotExist:
                log.error(f'was not able to find survey response for player {player.id}')
                continue
            else:
                # update cost with tax
                tax = sr.mechanism_cost + remaining_cost # todo this breaks frequently nonetype + float illegal
                sr.tax = tax
                sr.save()

    def calculate_other_tax(self, survey_responses=None):

        if not survey_responses:
            survey_responses = SurveyResponse.objects.filter(group_id=self.id)

        # total costs of participants
        # total_cost = sum(survey_responses.values_list('mechanism_cost', flat=True))

        c = self.get_set_c()
        g = self.get_g()

        non_participant_cost = (c + g) / (Constants.big_n - Constants.small_n)

        for player in self.get_players():

            if player.id_in_group == 1:
                continue

            try:
                sr = survey_responses.get(player_id=player.id)

                # update non_participant code after round so that officer bonus can be applied after round
                if not sr.participant:
                    sr.tax = non_participant_cost
                    rebate = 0
                else:
                    rebate = Constants.rebate
                    sr.tax = sr.mechanism_cost - rebate

                sr.rebate = rebate
                sr.save()

            except SurveyResponse.DoesNotExist:
                SurveyResponse.objects.create(player=player, group=self, tax=non_participant_cost, participant=False)
            else:
                pass

    def calculate_taxes(self):

        if Constants.dt_method == 0:
            self.calculate_survey_tax()
        elif Constants.dt_method == 1:
            self.calculate_ogl_tax()
        elif Constants.dt_method == 2:
            self.calculate_other_tax()
        elif Constants.dt_method == 3:
            self.calculate_other_tax()
        else:
            log.error(f'Could not determine dt_method for group {self.id}')

    def apply_taxes(self):
        # we need to run the calculate functions again to take into account the officer bonuses
        self.calculate_taxes()

        try:
            survey_responses = SurveyResponse.objects.filter(group=self)
        except SurveyResponse.DoesNotExist:
            log.error(f"could not get any survey responses while applying taxes for group {self.id}")
            return
        else:
            assert survey_responses.count() > 0

        for player in self.get_players():
            # officers never pay tax

            if player.id_in_group == 1:
                continue

            try:
                sr = survey_responses.get(player_id=player.id)
            except SurveyResponse.DoesNotExist:
                log.error(f"could not map survey response to player {player.id} while applying tax")
            else:
                player.balance -= sr.tax
                player.save()

    def get_officer_bonus(self):

        try:
            officer = self.get_player_by_id(1)

        except Player.DoesNotExist:
            log.error(f'Officer does not exist for group {self.id}')
            return 0
        else:
            return officer.income


def randomize_location():
    return randrange(Constants.steal_token_positions)+1


class Player(BasePlayer):
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    map = models.IntegerField(initial=0)
    last_updated = models.FloatField(blank=True)
    roi = models.IntegerField(initial=0)
    balance = models.FloatField(initial=Constants.civilian_start_balance)
    harvest_status = models.IntegerField(initial=0)
    harvest_screen = models.BooleanField(initial=True)
    income = models.IntegerField(initial=40)
    steal_start = models.IntegerField(initial=randomize_location)
    steal_count = models.IntegerField(initial=0)
    victim_count = models.IntegerField(initial=0)  # number of other players stealing from player
    steal_total = models.FloatField(initial=0)
    victim_total = models.FloatField(initial=0)
    ready = models.BooleanField(initial=False)

    def is_officer(self):
        if self.id_in_group == 1:
            return True
        else:
            return False

    def other_players(self):
        return self.get_others_in_group()

    def get_balance(self, time):
        # return calculated balance
        if self.roi == 0:
            return self.balance
        elif not self.last_updated:
            log.info(f'player: {self.pk} does not have last updated field initialized')
            return -99
        else:
            seconds_passed = time - self.last_updated
            return self.balance + (self.roi * seconds_passed)

    def increase_roi(self, time, direct):
        """
            direct argument determines which status count variable to update
        """
        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)

            # calculate balance
            player.balance = player.get_balance(time)  # we need to set balance with event time here boi
            player.last_updated = time
            # update roi
            player.roi += Constants.civilian_steal_rate

            if direct:
                # victim no longer being stolen from by a player
                player.steal_count += 1
            else:
                # culprit stealing from a victim
                player.victim_count -= 1

            player.save()

    def decrease_roi(self, time, direct):

        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)

            # calculate balance
            player.balance = player.get_balance(time)
            player.last_updated = time
            # update roi
            player.roi -= Constants.civilian_steal_rate

            if direct:
                player.steal_count -= 1
            else:
                player.victim_count += 1

            player.save()

    def civilian_fine(self):
        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)
            player.balance -= Constants.civilian_fine_amount
            player.save()

    def civilian_harvest(self):
        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)
            player.balance += self.income
            player.save()

    def officer_bonus(self):
        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)
            player.balance += self.income

            player.save()

    def officer_reprimand(self):
        with transaction.atomic():
            player = Player.objects.select_for_update().get(pk=self.pk)
            player.balance -= Constants.officer_reprimand_amount
            player.save()


class DefendToken(Model):
    group = ForeignKey(Group, on_delete='CASCADE')
    number = models.IntegerField()
    map = models.IntegerField(initial=0)
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    x2 = models.FloatField(initial=0)
    y2 = models.FloatField(initial=0)
    last_updated = models.FloatField(blank=True)
    slot = models.IntegerField(initial=-1)

    def to_dict(self):
        return {"number": self.number, "map": self.map, "x": self.x, "y": self.y}


class GameData(Model):
    event_time = models.FloatField()
    p = models.IntegerField(initial=0)
    g = models.IntegerField(initial=0)
    s = models.IntegerField(initial=0)
    round_number = models.IntegerField(initial=0)
    jdata = JSONField()


class SurveyResponse(Model):
    player = ForeignKey(Player, on_delete='CASCADE')
    group = ForeignKey(Group, on_delete='CASCADE')
    valid = models.BooleanField(initial=False)
    mechanism_cost = models.FloatField(null=True, default=None)
    total = models.IntegerField(initial=0)
    response = JSONField(null=True)
    participant = models.BooleanField(initial=False)
    # tax is calculated multiple times.
    # This field is convenience to hold latest calculation without overwriting cost field
    tax = models.FloatField(initial=0)
    rebate = models.IntegerField(null=True, default=None)

    @classmethod
    def calculate_thetas(cls, survey_responses, total):
        results = dict()

        for sr in survey_responses:
            x = 0
            player_id = sr.player_id
            eee = sr.total

            temp_total = total
            temp_total -= eee

            for sr2 in survey_responses:
                if sr2.player_id == player_id:
                    continue

                ptotal = sr2.total
                # if player_id == sr2.player_id:
                #     ptotal += 1

                x += (ptotal - 1 / (Constants.small_n - 1) * (temp_total)) ** 2

            results[sr.player_id] = (Constants.gamma / 2) * (1 / (Constants.small_n - 2)) * x

        return results

    @classmethod
    def calculate_ogl(cls, survey_responses):

        costs_results = dict()
        totals_results = dict()

        total = safe_list_sum(survey_responses.values_list('total', flat=True))

        log.info(f"total token count {total}")

        theta_results = SurveyResponse.calculate_thetas(survey_responses, total)
        log.info(f'theta results {theta_results}')

        for sr in survey_responses:
            player_sum = sr.total

            log.info(f"player sum {player_sum}")

            theta = theta_results[sr.player_id] if Constants.dt_method <= 1 else 0  # todo: make this easier to identify/change easily for testing

            ogl_results = (Constants.dt_q / Constants.big_n) * total + (Constants.gamma/2) * (Constants.small_n / (Constants.small_n-1)) * (player_sum - (1/Constants.small_n) * total)**2 - theta

            costs_results[sr.player_id] = ogl_results
            totals_results[sr.player_id] = player_sum

        return costs_results, totals_results

    @classmethod
    def csv_header(cls):
        if Constants.dt_method == 0:
            header = f"Player_Id,Integer,"
            for i in range(1, Constants.dt_range + 1):
                header += f"{i},"
        elif Constants.dt_method == 1:
            header = f"Player_Id,Integer,Value"
        elif Constants.dt_method > 1:
            header = f"Player_Id, Integer, Value"
        else:
            log.info(f"no csv header configured for method {Constants.dt_method}")
            return None
        return [header]

    def get_survey_value(self, index):
        if self.response.get(index):
            payment = self.response[index].total
            self.mechanism_cost = payment
            self.total = index
            self.save()
            return payment
        else:
            raise KeyError

    def csv_row(self):
        row = f"{self.player_id},{self.group_id},"
        if Constants.dt_method == 0:
            for key in self.response:
                row += f"{self.response[key]['total']},"
        elif Constants.dt_method == 1:
            row += f"{self.mechanism_cost}"
        elif Constants.dt_method > 1:
            row += f"{self.mechanism_cost}"
        else:
            log.info(f"CSVROW not configured for method {Constants.dt_method}")
            return

        return [row]

