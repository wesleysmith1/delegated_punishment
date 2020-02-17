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
    num_rounds = 1

    # civilian_income = 40  # y: todo make this change per harvest cycle (WILL CHANGE BETWEEN PERIOD GROUPS)
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

    civilian_incomes_one = [3, 5, 8, 10],
    civilian_incomes_two = [2, 3, 4, 15],
    officer_incomes = [0, 5, 10, 15],


class Subsession(BaseSubsession):

    def creating_session(self):

        # set session start time
        from delegated_punishment.helpers import date_now_milli
        session_start = date_now_milli()
        self.session.vars['session_start'] = session_start

        groups = self.get_groups()

        for g in groups:
            for p in g.get_players():
                # initialize balances list
                p.participant.vars['balances'] = []

                # demo session does not need further configuration
                if Constants.num_rounds != 1:

                    # set harvest amount for civilians
                    if p.id_in_group > 1:
                        incomes = Constants.civilian_incomes_one if self.round_number < 5 \
                            else Constants.civilian_incomes_two
                        i = incomes[0][p.id_in_group-2]
                        p.income = i
                    else:
                        officer = g.get_player_by_id(1)
                        i = Constants.officer_incomes[0][g.id-1]
                        officer.income = i

                else:
                    # todo remove this
                    officer = g.get_player_by_id(1)
                    officer.income = 10

            for i in range(Constants.defend_token_total):
                print('DEFEND TOKEN CREATED')
                DefendToken.objects.create(number=i + 1, group=g,)


class Group(BaseGroup):

    def generate_results(self):
        # players = self.get_players()
        # todo: this is here to prevent import error because Constants cannot be loaded.
        from delegated_punishment.generate_data import generate_csv
        generate_csv(
            self.id,
            self.subsession.round_number,
            self.subsession.session_id,
            self.session.vars['session_start']
        )


class Player(BasePlayer):
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    map = models.IntegerField(initial=0)
    last_updated = models.FloatField(blank=True)
    roi = models.IntegerField(initial=0)
    balance = models.FloatField(initial=200)
    harvest_status = models.IntegerField(initial=0)
    harvest_screen = models.BooleanField(initial=True)
    income = models.IntegerField(initial=40)

    def other_players(self):
        return self.get_others_in_group()

    def get_balance(self, time):
        # return calculated balance
        if self.roi == 0:
            return self.balance # this is incorrect man!
        elif not self.last_updated:
            return -99
        else:
            return self.balance + self.roi * (time - self.last_updated)

    def increase_roi(self, time):
        # calculate balance
        self.balance = self.get_balance(time) # we need to set balance with event time here boi
        self.last_updated = time
        # update roi
        self.roi += Constants.civilian_steal_rate

    def decrease_roi(self, time):
        # calculate balance
        self.balance = self.get_balance(time)
        self.last_updated = time
        # update roi
        self.roi -= Constants.civilian_steal_rate


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
