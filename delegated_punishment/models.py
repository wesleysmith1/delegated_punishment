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
from delegated_punishment.income_distributions import IncomeDistributions
from delegated_punishment.helpers import date_now_milli

import logging
log = logging.getLogger(__name__)

doc = """
"""


class Constants(BaseConstants):
    name_in_url = 'delegated_punishment'
    players_per_group = 6
    civilians_per_group = 5
    num_rounds = 12

    """Number of defend tokens officer starts with"""
    defend_token_total = 8

    """Fine when convicted"""
    civilian_fine_amount = 120
    """number of grain earned per second of stealing"""
    civilian_steal_rate = 16

    """Chance that an intersection outcome will be reviewed"""
    officer_review_probability = .25

    """P punishment for officer if innocent civilian is punished"""
    l = 1
    m = 80
    h = 320
    # treatment variables including tutorial
    officer_reprimand_amount = [m,m,m,m,m,m,m,l,l,l,l,l]

    """Officer income (bonus). One for each group"""
    officer_income = 20

    """ 
    this is the size of the tokens and maps are defined. 
    """
    defend_token_size = 152
    civilian_map_size = 200 * 1.5

    """Probability innocent and guilty are calculated when the number of investigation tokens is >= this number"""
    a_max = 6
    """todo: label this correctly... find out where this is from and why it is needed...."""
    beta = 18
    """
    Tutorial, game and results modal durations are defined here and passed to frontend
    """
    tutorial_duration_seconds = 1800
    game_duration_seconds = 180
    results_modal_seconds = 15
    start_modal_seconds = 15

    """"This defines how long after defend tokens have been placed, and when they can be moved again"""
    defend_pause_duration = 2000
    """
    this defines how long a steal token remains on a map before resetting to the 'steal home'
    """
    steal_timeout_milli = 2000
    """
    This is how long the steal token can actively steal continuously before being reset to the 'steal home'
    """
    steal_pause_duration = 1000
    """
    Steal tokens positions defines the number of slots inside the 'steal home' rectangle. Steal tokens can be loaded or 
    reset to any of the slots 
    """
    steal_token_slots = 20

    officer_start_balance = 800
    civilian_start_balance = 600


    # probability calculations
    # key=#probabilities -> innocent, culprit, prob nobody
    # the index
    calculated_probabilities = [
        (.18, .18, .28), # 0 defense tokens tokens
        (.15, .30, .25), # 1 defense ...
        (.12, .42, .22), # 2 ...
        (.09, .54, .19), # 3 ...
        (.06, .66, .16), # 4 ...
        (.03, .78, .13), # 5 ...
        (0, .9, .1), # 6 ...
        (0, .9, .1), # 7 ...
        (0, .9, .1), # 8 ...
    ]


class Subsession(BaseSubsession):

    def creating_session(self):
        """This is called once for each round"""

        # validate constants model
        try:
            assert Constants.civilians_per_group+1 == Constants.players_per_group
        except AssertionError:
            # log.error("Civilians must be 1 less than players per group in the Constants model")
            return

        # set session start time
        from delegated_punishment.helpers import date_now_milli
        session_start = date_now_milli()
        self.session.vars['session_start'] = session_start
        self.session.vars['session_date'] = datetime.datetime.today().strftime('%Y%m%d')

        groups = self.get_groups()

        config_key = self.session.config['civilian_income_config']
        round_incomes = IncomeDistributions.get_group_income_distribution(config_key, self.round_number)

        # this code is the terrible way that officer income is determined for session
        if self.round_number == 1:
            index = 0
            for gr in groups:

                officer_bonus = Constants.officer_income
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

            g.officer_reprimand_amount = Constants.officer_reprimand_amount[g.round_number - 1]

            for p in g.get_players():
                # initialize balances list
                p.participant.vars['balances'] = []
                p.participant.vars['steal_start'] = p.steal_start

                if p.is_officer():
                    p.balance = Constants.officer_start_balance

                # demo session does not need further configuration
                if Constants.num_rounds != 1:

                    # check if round is tutorial or trial round
                    if self.round_number < 3:
                        if p.id_in_group > 1:
                            p.income = self.session.config['tutorial_civilian_income']
                        else:
                            p.income = self.session.config['tutorial_officer_bonus']
                    else:
                        # set harvest amount for civilians
                        if p.id_in_group > 1:
                            income_index = p.id_in_group-2
                            p.income = round_incomes[income_index]
                        else:
                            # is officer
                            p.income = p.participant.vars['officer_bonus']

                else:
                    # only one round being played
                    officer = g.get_player_by_id(1)
                    officer.income = self.session.config['tutorial_officer_bonus']

            for i in range(Constants.defend_token_total):
                DefendToken.objects.create(number=i+1, group=g,)


class GameStatus:
    SYNC = 0
    INFO = 1
    ACTIVE = 2
    RESULTS = 3
    CHOICES = (
        (SYNC, 'Sync'),
        (INFO, 'Start'),
        (ACTIVE, 'Active'),
        (RESULTS, 'Results'),
    )


class Group(BaseGroup):
    game_start = models.FloatField(blank=True)
    officer_bonus = models.IntegerField(initial=0)
    # counters
    officer_bonus_total = models.IntegerField(initial=0)
    civilian_fine_total = models.IntegerField(initial=0)
    officer_reprimand_total = models.IntegerField(initial=0) # count variable
    intercept_total = models.IntegerField(initial=0)

    game_status = models.IntegerField(choices=GameStatus.CHOICES, default=GameStatus.SYNC)

    officer_reprimand_amount = models.IntegerField() # dynamic treatment variable that can change round to round

    @classmethod
    def intersection_update(cls, group_id, bonus, fine, reprimand, intercept):
        with transaction.atomic():
            me = Group.objects.select_for_update().get(id=group_id)
            me.officer_bonus_total += bonus
            me.civilian_fine_total += fine
            me.officer_reprimand_total += reprimand
            me.intercept_total += intercept
            me.save()
            return dict(bonus=me.officer_bonus_total, fine=me.civilian_fine_total, reprimand=me.officer_reprimand_total, intercept=me.intercept_total)

    def is_tutorial(self):
        return self.round_number == 1

    def balance_update(self, time):
        players = self.get_players()
        # players = Player.objects.filter(group_id=self.id).values_list('map', 'last_updated', 'balance', 'roi', 'id_in_group', 'victim_count', 'steal_count')

        balance_update = dict()

        # maps being stolen from
        active_maps = {}

        for i in range(1, Constants.players_per_group+1):
            active_maps[i] = 0 #todo make a list comphrension for imporved speed

        for player in players:
            if player.map > 0:
                active_maps[player.map] += 1

            balance_update[player.id_in_group] = dict(
                balance=player.get_balance(time),
                map=player.map, # 
                victim_count=player.victim_count,
                steal_count=player.steal_count,
            )
            balance_update['active_maps'] = active_maps

        return balance_update

    def generate_results(self):
        """generate game results and convert to csv"""
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

        config_key = self.session.config['civilian_income_config']
        incomes = IncomeDistributions.get_group_income_distribution(config_key, self.round_number)

        meta_data = dict(
            round_number=self.subsession.round_number,
            session_id=self.subsession.session_id,
            steal_starts=steal_starts,
            session_start=self.session.vars['session_start'],
            session_date=self.session.vars['session_date'],
            group_pk=self.pk,
            group_id=group_id,
            officer_bonus=officer_bonus,
            income_distribution=incomes,  # todo: this needs to reflect values not keys
            player_ids_in_session=player_ids_in_session,
            reprimand=self.officer_reprimand_amount, # group reprimand amount
        )

        # todo: this is here to prevent import error because Constants cannot be loaded.
        from delegated_punishment.generate_data import generate_csv
        generate_csv(self.session, self.subsession, meta_data)


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
    income = models.IntegerField(initial=40) #todo: this should not be hardcoded
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

    def stop_stealing(self):
        """called during vars_for_template on game page. this prevents stealing continuously"""
        if self.map == 0:
            return

        event_time = date_now_milli()

        game_data_dict = dict({'steal_reset': -1})

        # update victim
        victim = Player.objects.get(group_id=self.group_id, id_in_group=self.map)
        victim.increase_roi(event_time, False)
        game_data_dict.update({
            "victim": victim.id_in_group,
            "victim_roi": victim.roi,
            "victim_balance": victim.balance,
        })

        # update player
        self.decrease_roi(event_time, True)
        self.map = 0
        self.harvest_screen = True
        self.save()

        game_data_dict.update({
            "event_type": "steal_reload",  # todo: this needs to be reviewed by jordan or something
            "event_time": event_time,
            "harvest_screen": self.harvest_screen,
            "player": self.id_in_group,
            "player_roi": self.roi,
            "player_balance": self.balance,
        })

        GameData.objects.create(
            event_time=event_time,
            p=self.id,
            g=self.group_id,
            s=self.session_id,
            round_number=self.round_number,
            jdata=game_data_dict,
        )

    def get_balance(self, time):
        # return calculated balance
        if self.roi == 0:
            return self.balance
        elif not self.last_updated:
            # log.info(f'player: {self.pk} does not have last updated field initialized')
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
            # todo: why is this explicit conversion required here?
            player.roi = int(player.roi + Constants.civilian_steal_rate)

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
            player.roi = int(player.roi - Constants.civilian_steal_rate)

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
            player.balance -= self.group.officer_reprimand_amount
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
