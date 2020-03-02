import datetime
from delegated_punishment.models import Constants
import os
import math


def date_now_milli():
    return (datetime.datetime.now() - Constants.epoch).total_seconds()


def write_session_dir(session_identifier):
    path = 'data/session_' + session_identifier + '/'

    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the directory %s failed" % path)
            path = 'data/'
        else:
            print("Successfully created the directory %s " % path)

    return path


class TimeFormatter:
    """This class accepts seconds and returns MM:SS.ss since first event"""
    def __init__(self, start):
        self.start = start

    def format(self, time):
        t = time - self.start
        minutes = math.floor(t / 60)
        seconds = t % 60
        return "{}:{}".format(minutes, seconds)