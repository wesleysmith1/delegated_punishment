from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
)


class Constants(BaseConstants):
    name_in_url = 'survey'
    players_per_group = None
    num_rounds = 1

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    first_name = models.StringField()
    last_name = models.StringField()

    strategy = models.StringField(label="How did you make your decisions during the experiment?")
    feedback = models.StringField(label="Is there anything else you would like to tell the experimenters about this experiment?")

    participant_code = models.StringField()
    id_in_session = models.IntegerField()


