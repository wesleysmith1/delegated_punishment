from . import pages
from ._builtin import Bot
from .models import Constants
from otree.api import Submission

import logging
log = logging.getLogger(__name__)


class PlayerBot(Bot):

    cases = [
        'success',  # players agree on an amount under the threshold
        'greedy',  # players ask for too much so end up with nothing
    ]

    def play_round(self):

        yield (pages.Intermission)

        yield Submission(pages.Game, dict(), timeout_happened=True)