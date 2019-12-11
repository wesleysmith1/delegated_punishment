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


doc = """
This bargaining game involves 2 players. Each demands for a portion of some
available amount. If the sum of demands is no larger than the available
amount, both players get demanded portions. Otherwise, both get nothing.
"""


class Constants(BaseConstants):
    name_in_url = 'bargaining' #todo
    players_per_group = 5
    num_rounds = 1

    instructions_template = 'bargaining/instructions.html'

    # amount_shared = c(100)


class Subsession(BaseSubsession):
    pass


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
    lives = models.IntegerField(initial=5)
    isIt = models.BooleanField(initial=False)
    location = models.IntegerField() #todo can this be null?

    def other_player(self):
        return self.get_others_in_group()
