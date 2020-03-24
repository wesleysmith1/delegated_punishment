from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from .models import Constants
from otree.api import Submission


class PlayerBot(Bot):
    def play_round(self):
        # compete price
        yield Submission(pages.Welcome, dict(), check_html=False)
