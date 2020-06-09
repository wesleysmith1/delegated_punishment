import datetime
import json

from django.contrib.postgres.fields import JSONField
from django.db import transaction
from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)
from otree.db.models import Model, ForeignKey, DecimalField
from random import randrange

from delegated_punishment.helpers import safe_list_sum, format_template_numbers, date_now_milli
from delegated_punishment.mechanism import OglMechanism, OtherMechanism, SurveyMechanism

import logging
log = logging.getLogger(__name__)

from decimal import Decimal

doc = """
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment'
    players_per_group = 9
    num_rounds = 10

    """Number of defend tokens officer starts with"""
    defend_token_total = 8

    # officer_intersection_payout = 10  # b: how much officer makes for intersection

    """Fine when convicted"""
    civilian_fine_amount = 120
    """number of grain earned per second of stealing"""
    civilian_steal_rate = 13

    """Chance that an intersection outcome will be reviewed"""
    officer_review_probability = .33
    """P punishment for officer if innocent civilian is punished"""
    officer_reprimand_amount = 600

    """Civilian incomes for each group's players"""
    civilian_incomes_low = [38, 39, 40, 41, 43, 99, 99, 99]  # todo: add correct balances here
    civilian_incomes_high = [57, 41, 38, 34, 31, 99, 99, 99]

    """Officer incomes. One for each group"""
    # officer_incomes = [0, 10, 20]
    officer_incomes = [180, 180, 180]
    # officer_incomes = [0, 180, 600]

    """ 
    this is the size of the tokens is defined. 
    When changing values also update officer.css file 
    """
    defend_token_size = 68
    civilian_map_size = 200

    """Probability innocent and guilty are calculated when the number of investigation tokens is >= this number"""
    a_max = 6
    """Guilty probability when """
    beta = .9

    """
    Tutorial, game and results modal durations are defined here and passed to frontend
    """
    tutorial_duration_seconds = 1800
    game_duration_seconds = 198
    results_modal_seconds = 30
    start_modal_seconds = 10

    """
    this defines how long a steal token remains on a map before resetting to the 'steal home'
    """
    steal_timeout_milli = 1000

    """
    Steal tokens positions defines the number of slots inside the 'steal home' rectangle. Steal tokens can be loaded or 
    reset to any of the slots 
    """
    steal_token_slots = 20

    officer_start_balance = 1000
    civilian_start_balance = 0

    dt_range = 10
    dt_payment_max = 10
    big_n = 8

    dt_mechanism_seconds = 30  # seconds

    """
    # debug
    dt_mechanism_seconds = 120  # seconds
    results_modal_seconds = 30  # 30
    start_modal_seconds = 10
    """

    # Uncomment a block below for Mechanism Configuration
    """
    # Survey
    dt_method = 0
    small_n = 4
    gamma = -1
    omega = -1
    dt_rebate = 0
    dt_e0 = None
    dt_q = 8
    """

    # """
    #OGL
    dt_method = 1
    small_n = 8
    gamma = 9
    omega = 100
    dt_rebate = 0
    dt_e0 = 0
    dt_q = 8
    # """

    """
    #MGL - Statistical 
    dt_method = 2
    small_n = 4
    gamma = 9
    omega = 100
    dt_rebate = 20
    dt_e0 = 0
    dt_q = 8
    """

    """
    #MGL - Experimental
    dt_method = 3
    small_n = 4
    gamma = 9
    omega = 2
    dt_rebate = 20
    dt_e0 = 8
    dt_q = 8
    """

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
    defend_token_cost = models.DecimalField(initial=0, max_digits=10, decimal_places=5) # maybe this hsould be moved over to tha mechanism table
    officer_bonus_total = models.IntegerField(initial=0)
    civilian_fine_total = models.IntegerField(initial=0)
    big_c = models.DecimalField(blank=True, default=None, max_digits=10, decimal_places=5) # maybe this hsould be moved over to tha mechanism table

    # todo: turn this into a proper factory or part of a generator. :)
    @classmethod
    def round_outcome_variables(cls, group, player):

        try:
            response = SurveyResponse.objects.get(player=player)
        except SurveyResponse.DoesNotExist:
            response = None

        if Constants.dt_method == 0:
            vars = SurveyMechanism().result_vars(group, player, response)
        elif Constants.dt_method == 1:
            vars = OglMechanism().result_vars(group, player, response)
        elif Constants.dt_method > 1:
            vars = OtherMechanism().result_vars(group, player, response)
        else:
            vars = {}
            # todo: there was an error:
            pass

        return vars

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

            x = SurveyMechanism().start_vars(
                id_in_group,
                self.defend_token_total,
                self.defend_token_cost,
                response,
            )

        elif Constants.dt_method == 1:

            x = OglMechanism().start_vars(
                id_in_group,
                self.defend_token_total,
                self.defend_token_cost,
                response,
            )

        elif Constants.dt_method > 1:

            x = OtherMechanism().start_vars(
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
            sum_costs = Decimal(safe_list_sum(SurveyResponse.objects.filter(group=self).values_list('mechanism_cost', flat=True)))

        # TODO:
        # rebate * small_n will change if rebates require some form of validaiton.
        c = self.defend_token_total * Constants.dt_q + (Constants.dt_rebate * Constants.small_n) - sum_costs
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

        all_participants_fee = Decimal((c + g) / Constants.big_n)

        self.defend_token_cost = Decimal(all_participants_fee * Constants.big_n)

        for player in self.get_players():

            if player.id_in_group == 1:
                continue

            try:
                sr = survey_responses.get(player_id=player.id)
                sr.mechanism_cost = Decimal(all_participants_fee)
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
        remaining_cost = Decimal(str(g)) / Decimal(str(Constants.big_n))

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
                tax = Decimal(sr.mechanism_cost + remaining_cost)  # todo this breaks frequently nonetype + float illegal
                sr.tax = tax
                sr.save()

    def calculate_other_tax(self, survey_responses=None):

        if not survey_responses:
            survey_responses = SurveyResponse.objects.filter(group_id=self.id)

        # total costs of participants
        # total_cost = sum(survey_responses.values_list('mechanism_cost', flat=True))

        c = self.get_set_c()
        g = self.get_g()

        non_participant_cost = Decimal((c + g) / (Constants.big_n - Constants.small_n))

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
                    rebate = Constants.dt_rebate
                    sr.tax = Decimal(sr.mechanism_cost)

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
                # todo: this should checked later. we may make balance field a decimal type
                # rebate is only applicable for MGL mechanisms
                player.balance = float(Decimal(player.balance) - sr.tax + sr.rebate)
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
    return randrange(Constants.steal_token_slots)+1


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
    mechanism_cost = models.DecimalField(initial=0, max_digits=10, decimal_places=5)
    total = models.IntegerField(initial=0)
    response = JSONField(null=True)
    participant = models.BooleanField(initial=False)
    # tax is calculated multiple times.
    # This field is convenience to hold latest calculation without overwriting cost field
    tax = models.DecimalField(max_digits=10, decimal_places=5)
    rebate = models.IntegerField(initial=0)

    @classmethod
    def calculate_thetas(cls, survey_responses, total):
        results = dict()

        for sr in survey_responses:
            x = Decimal(0)
            player_id = sr.player_id
            eee = Decimal(sr.total)

            temp_total = Decimal(total)
            temp_total -= eee

            for sr2 in survey_responses:
                if sr2.player_id == player_id:
                    continue

                ptotal = Decimal(sr2.total)
                # if player_id == sr2.player_id:
                #     ptotal += 1

                x = x + Decimal((ptotal - Decimal(1) / (Constants.small_n - Decimal(1)) * temp_total) ** 2)

            results[sr.player_id] = Decimal(Constants.gamma / 2) * Decimal(1 / (Constants.small_n - 2)) * x

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

            ogl_results = Decimal((Constants.dt_q / Constants.big_n) * total + (Constants.gamma/2) * (Constants.small_n / (Constants.small_n-1)) * (player_sum - (1/Constants.small_n) * total)**2) - theta

            costs_results[sr.player_id] = ogl_results
            totals_results[sr.player_id] = player_sum

        return costs_results, totals_results

    def get_survey_value(self, index):
        if self.response.get(index):
            payment = Decimal(self.response[index].total)
            self.mechanism_cost = payment
            self.total = index
            self.save()
            return payment
        else:
            raise KeyError

    def survey_row(self):
        row = f"{self.player_id},{self.player.pariticipant_id},{self.group_id},"
        for key in self.response:
            row += f"{self.response[key]['total']},"

        return [row]


class MechanismInput(Model):
    player = ForeignKey(Player, on_delete='CASCADE')
    participant_id = models.IntegerField()
    group = ForeignKey(Group, on_delete='CASCADE')
    value = models.IntegerField(initial=0)
    created_at = models.FloatField()

    @classmethod
    def record(cls, value, player_id, group_id):
        creation_time = date_now_milli()
        MechanismInput.objects.create(value=value, player_id=player_id, group_id=group_id, created_at=creation_time)

    def gl_row(self):
        row = f"{self.group_id},{self.participant_id},{self.player_id},{self.value},{self.created_at}"
        return [row]
