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
This Delegated Punishment game involves 2 players. Each demands for a portion of some
available amount. If the sum of demands is no larger than the available
amount, both players get demanded portions. Otherwise, both get nothing.
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment' #todo
    players_per_group = 5
    num_rounds = 1 #todo

    instructions_template = 'delegated_punishment/instructions.html'

    # amount_shared = c(100)

class Subsession(BaseSubsession):

    def before_session_starts(self):
        # OfficerToken.objects.all().delete()
        groups = self.get_groups()

        for g in groups:    
            for i in range(10):
                OfficerToken.objects.create(number=i, group=g)

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


class Player(BasePlayer):
    # role
    x = models.FloatField(blank=True)
    y = models.FloatField(blank=True)
    property = models.IntegerField(blank=True)
    last_updated = models.IntegerField(blank=True)
    status = models.IntegerField(
        choices=[
            [1, 'Harvest'],
            [2, 'Steal'],
        ]
    )
    roi = models.IntegerField()
    balance = models.IntegerField(initial=0)

    def other_players(self):
        return self.get_others_in_group()

class OfficerToken(Model):
    group = ForeignKey(Group, on_delete='CASCADE')
    number = models.IntegerField()
    property = models.IntegerField(blank=True)
    x = models.FloatField(blank=True)
    y = models.FloatField(blank=True)
