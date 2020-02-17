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

    name = models.StringField(label="Please enter your name:")

    race_ethnicity = models.StringField(
        choices=['White', 'Black or African American', 'Asian', 'Indian or Pacific Islander', 'Hispanic', 'Multiracial', 'Other, Prefer not to say'],
        label="What is your race/ethnicity",
        widget=widgets.RadioSelect,
    )

    confused = models.StringField(
        choices=['Yes', 'No', 'Prefer not to say'],
        label="Were you confused by anything in the experiment?",
        widget=widgets.RadioSelect,
    )

    gender = models.StringField(
        choices=[['Male', 'Male'], ['Female', 'Female']],
        label='What is your gender?',
        widget=widgets.RadioSelect,
    )

    confused_explanation = models.StringField(blank=True, label="If yes, what confused you?")
    strategy = models.StringField(label="How did you make your decisions during the experiment?")
    feedback = models.StringField(label="Is there anything else you would like to tell the experimenters about this experiment?")

    payout = models.IntegerField(initial=0)


