import datetime

from django.contrib.postgres.fields import JSONField
from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)
from otree.db.models import Model, ForeignKey

doc = """
This Delegated Punishment game involves 5 players. Each demands for a portion of some
available amount. If the sum of demands is no larger than the available
amount, both players get demanded portions. Otherwise, both get nothing.
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment'
    players_per_group = 5
    num_rounds = 8

    civilian_steal_rate = 6  # S: amount of grain stolen per second (CONSTANT ACROSS GROUPS AND PERIODS)
    civilian_conviction_amount = 540

    # officer_intersection_payout = 10  # b: how much officer makes for intersection
    officer_review_probability = .1  # THETA: chance that an intersection result will be reviewed
    officer_reprimand_amount = 100  # P punishment for officer if innocent civilian is punished
    defend_token_total = 9

    epoch = datetime.datetime.utcfromtimestamp(0)
    instructions_template = 'delegated_punishment/instructions.html'

    defend_token_size = 36  # this is the size of the tokens that players with role of officer drag around
    civilian_map_size = 240

    civilian_incomes_low = [3, 5, 8, 10],
    civilian_incomes_high = [2, 3, 4, 15],
    officer_incomes = [0, 5, 10, 15],

    start_balance = 200


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
                officer_bonus = Constants.officer_incomes[0][index]
                officer = gr.get_player_by_id(1)
                officer.income = officer_bonus
                officer_participant = officer.participant
                officer_participant.vars['officer_bonus'] = officer_bonus
                # officer_participant.save()
                index += 1

        for g in groups:
            for p in g.get_players():
                # initialize balances list
                p.participant.vars['balances'] = []
                p.participant.vars['steal_start'] = p.steal_start

                # demo session does not need further configuration
                if Constants.num_rounds != 1:

                    # set harvest amount for civilians
                    if p.id_in_group > 1:
                        incomes = Constants.civilian_incomes_low if self.round_number < 5 \
                            else Constants.civilian_incomes_high
                        i = incomes[0][p.id_in_group-2]
                        p.income = i
                    else:
                        # is officer
                        p.income = p.participant.vars['officer_bonus']

                else:
                    # todo remove this
                    officer = g.get_player_by_id(1)
                    officer.income = 10

            for i in range(Constants.defend_token_total):
                d = DefendToken.objects.create(number=i+1, group=g,)
                # print('DEFEND TOKEN CREATED FOR GROUP {} | ID: {}'.format(g.id, d.id))


class Group(BaseGroup):

    def balance_update(self, time):
        players = self.get_players()
        balance_update = dict()

        # maps being stolen from
        active_maps = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0
        }

        for player in players:
            if player.map > 0:
                active_maps[player.map] = 1

            balance_update[player.id_in_group] = dict(
                balance=player.get_balance(time),
                map=player.map,
                # victim_count=player.victim_count,
                # steal_count=player.steal_count,
            )
            balance_update['active_maps'] = active_maps

        return balance_update

    def generate_results(self):
        players = self.get_players()

        # Initial civilian steal locations for csv
        steal_starts = [-1, -1, -1, -1, -1]
        for p in players:
            steal_starts[p.id_in_group-1] = p.participant.vars['steal_start']

        officer_bonus = self.get_player_by_id(1).participant.vars['officer_bonus']

        if self.session.config['low_to_high']:
            if self.subsession.round_number < 5:
                income_distribution = Constants.civilian_incomes_low
            else:
                income_distribution = Constants.civilian_incomes_high
        else:
            if self.subsession.round_number < 5:
                income_distribution = Constants.civilian_incomes_high
            else:
                income_distribution = Constants.civilian_incomes_low


        period_info = dict(
            round_number=self.subsession.round_number,
            session_id=self.subsession.session_id,
            steal_starts=steal_starts,
            session_start=self.session.vars['session_start'],
            session_date=self.session.vars['session_date'],
            group_id=self.pk,
            officer_bonus=officer_bonus,
            income_distribution=income_distribution,
        )

        # todo: this is here to prevent import error because Constants cannot be loaded.
        from delegated_punishment.generate_data import generate_csv
        generate_csv(period_info)

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
    balance = models.FloatField(initial=Constants.start_balance)
    harvest_status = models.IntegerField(initial=0)
    harvest_screen = models.BooleanField(initial=True)
    income = models.IntegerField(initial=40)
    steal_start = models.IntegerField(initial=rand_location)
    steal_count = models.IntegerField(initial=0)
    victim_count = models.IntegerField(initial=0)  # number of other players stealing from player
    steal_total = models.FloatField(initial=0)
    victim_total = models.FloatField(initial=0)


    def other_players(self):
        return self.get_others_in_group()

    def get_balance(self, time):
        # return calculated balance
        if self.roi == 0:
            return self.balance
        elif not self.last_updated:
            return -99
        else:
            time_passed = time - self.last_updated
            return self.balance + (self.roi * time_passed)

    def increase_roi(self, time, direct):
        """
            direct argument determines which status count variable to update
        """
        # calculate balance
        self.balance = self.get_balance(time)  # we need to set balance with event time here boi
        self.last_updated = time
        # update roi
        self.roi += Constants.civilian_steal_rate

        if direct:
            # victim no longer being stolen from by a player
            self.victim_count -= 1
        else:
            # culprit stealing from a victim
            self.steal_count += 1

    def decrease_roi(self, time, direct):
        # calculate balance
        self.balance = self.get_balance(time)
        self.last_updated = time
        # update roi
        self.roi -= Constants.civilian_steal_rate

        if direct:
            self.steal_count -= 1
        else:
            self.victim_count += 1


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
