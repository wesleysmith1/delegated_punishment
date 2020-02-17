import datetime
from delegated_punishment.models import Constants


def date_now_milli():
    return (datetime.datetime.now() - Constants.epoch).total_seconds()