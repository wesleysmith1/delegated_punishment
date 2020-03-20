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
from decimal import *

doc = """
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment'
    players_per_group = 6
    num_rounds = 10
    # num_rounds = 1  # testing purposes

    # officer_intersection_payout = 10  # b: how much officer makes for intersection
    defend_token_total = 8

    epoch = datetime.datetime.utcfromtimestamp(0)

    start_balance = 0

    # these variables will be subject to change the most
    civilian_fine_amount = 120
    civilian_steal_rate = 13  # S: amount of grain stolen per second (CONSTANT ACROSS GROUPS AND PERIODS)

    officer_review_probability = .33  # THETA: chance that an intersection result will be reviewed
    officer_reprimand_amount = 600  # P punishment for officer if innocent civilian is punished

    civilian_incomes_low = [38, 39, 40, 41, 43]
    civilian_incomes_high = [57, 41, 38, 34, 31]
    # officer_incomes = [0, 10, 20]
    officer_incomes = [180, 180, 180]
    # officer_incomes = [0, 180, 600]

    # also change in officer.css
    defend_token_size = 68  # this is the size of the tokens that players with role of officer drag around
    civilian_map_size = 200

    beta = .9
    a_max = 6

    tutorial_duration = 1800000
    game_duration_seconds = 198

    officer_start_balance = 1000

    steal_timeout_duration = 200000


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

            for i in range(Constants.defend_token_total):
                DefendToken.objects.create(number=i+1, group=g,)


class Group(BaseGroup):
    game_start = models.FloatField(blank=True)
    officer_bonus = models.IntegerField(initial=0)
    players_ready = models.IntegerField(initial=0)

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

    def group_ready(self):
        """Have all player pages loaded"""
        if self.players_ready == Constants.players_per_group:
            return True
        return False

    def balance_update(self, time):
        players = self.get_players()
        balance_update = dict()

        # maps being stolen from
        active_maps = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
        }

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
        player_ids_in_session = steal_starts = [-1, -1, -1, -1, -1, -1]
        for p in players:
            steal_starts[p.id_in_group-1] = p.participant.vars['steal_start']
            player_ids_in_session[p.id_in_group-1] = p.participant.id_in_session

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

        # try:
        #     generate_csv(period_info)
        # except:
        #     print('THERE WAS AN ERROR WITH CSV GENERATION FOR PERIOD: {}'.format(self.subsession.round_number))


def rand_location():
    from random import randrange
    return randrange(Constants.defend_token_total)+1


class Player(BasePlayer):
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    map = models.IntegerField(initial=0)
    last_updated = models.FloatField(blank=True)
    roi = models.IntegerField(initial=0)
    balance = models.FloatField(initial=Constants.start_balance) #todo: we can make this a decimal field btw
    harvest_status = models.IntegerField(initial=0)
    harvest_screen = models.BooleanField(initial=True)
    income = models.IntegerField(initial=40)
    steal_start = models.IntegerField(initial=rand_location)
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
            return -99 #todo fix this shit
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


class DefendToken(Model):
    group = ForeignKey(Group, on_delete='CASCADE')
    number = models.IntegerField()
    map = models.IntegerField(initial=0)
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    x2 = models.FloatField(initial=0)
    y2 = models.FloatField(initial=0)
    last_updated = models.FloatField(blank=True)

    def __str__(self):
        str(self.x) + "," + str(self.y)

    def to_dict(self):
        return {"number": self.number, "map": self.map, "x": self.x, "y": self.y}


class GameData(Model):
    event_time = models.FloatField()
    p = models.IntegerField(initial=0)
    g = models.IntegerField(initial=0)
    s = models.IntegerField(initial=0)
    round_number = models.IntegerField(initial=0)
    jdata = JSONField()
