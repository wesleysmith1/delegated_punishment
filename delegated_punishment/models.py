import datetime
from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
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
    num_rounds = 1  # todo

    civilian_income = 40  # y: todo make this change per harvest cycle (WILL CHANGE BETWEEN PERIOD GROUPS)
    civilian_steal_rate = 6  # S: amount of grain stolen per second (CONSTANT ACROSS GROUPS AND PERIODS)
    civilian_conviction_amount = 540

    officer_intersection_payout = 10  # b: how much officer makes for intersection
    officer_review_probability = .1  # THETA: chance that an intersection result will be reviewed
    officer_reprimand_amount = 100  # P punishment for officer if innocent civilian is punished
    officer_token_total = 9

    epoch = datetime.datetime.utcfromtimestamp(0)
    instructions_template = 'delegated_punishment/instructions.html'  # todo this may be the cuase of the linux issue not finding the file due to case sensitivity

    officer_token_size = 36  # this is the size of the tokens that players with role of officer drag around
    civilian_map_size = 240


class Subsession(BaseSubsession):

    def before_session_starts(self):
        # DefendToken.objects.all().delete()
        groups = self.get_groups()

        for g in groups:
            for i in range(Constants.officer_token_total):
                DefendToken.objects.create(number=i + 1, group=g, )


class Group(BaseGroup):
    pass

    # def set_payoffs(self):
    #     players = self.get_players()
    #     self.total_requests = sum([p.request for p in players])
    #     if self.total_requests <= Constants.amount_shared:
    #         for p in players:
    #             p.payoff = p.request
    #     else:
    #         for p in players:
    #             p.payoff = c(0)


def date_now_milli():  # todo: move this to another file
    return (datetime.datetime.now() - Constants.epoch).total_seconds() * 1000.0

class Player(BasePlayer):
    # role
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    map = models.IntegerField(initial=0)
    last_updated = models.FloatField(blank=True)
    status = models.IntegerField(
        choices=[
            [1, 'Harvest'],
            [2, 'Steal'],
        ]
    )
    roi = models.IntegerField(initial=0)  # rate of increase per millisecond
    balance = models.FloatField(initial=0)
    harvest_status = models.IntegerField(initial=0)

    def other_players(self):
        return self.get_others_in_group()

    def get_balance(self):
        # return calculated balance
        if self.roi == 0:
            return self.balance
        elif not self.last_updated:
            return -99
        else:
            # return self.balance + self.roi * (((date_now_milli() - self.last_updated) / 1000) % 60)
            return self.balance + self.roi * ((date_now_milli() - self.last_updated) / 1000)

    def increase_roi(self, time):
        # calculate balance
        self.balance = self.get_balance()
        self.last_updated = time
        # update roi
        self.roi += Constants.civilian_steal_rate

        # self.save()  # Consider overriding the save method or something

    def decrease_roi(self, time):
        # calculate balance
        self.balance = self.get_balance()
        self.last_updated = time
        # update roi
        self.roi -= Constants.civilian_steal_rate

        # self.save()  # Consider overriding the save method or something


class DefendToken(Model):
    group = ForeignKey(Group, on_delete='CASCADE')
    number = models.IntegerField()
    map = models.IntegerField(initial=0)
    x = models.FloatField(initial=0)
    y = models.FloatField(initial=0)
    last_updated = models.FloatField(blank=True)

    def __str__(self):
        str(self.x) + "," + str(self.y)

    def to_dict(self):
        return {"number": self.number, "map": self.map, "x": self.x, "y": self.y}

from django.contrib.postgres.fields import JSONField

class GameData(Model):
    p = models.IntegerField(initial=0)
    g = models.IntegerField(initial=0)
    jdata = JSONField()
