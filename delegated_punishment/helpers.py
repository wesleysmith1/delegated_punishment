import time
import os
import math
from decimal import *
from random import randrange
getcontext().prec = 17


def date_now_milli():
    # returns seconds
    return time.time()
    # return double
    # Decimal(repr(time.time()))

# +def get_theta(survey_responses, total, n, gamma):
# +    theta_results = dict()
# +    for sr in survey_responses:
# +        x = 0
# +        for sr2 in survey_responses:
# +            if sr2.player_id == sr.player_id:
# +                continue
# +            x += (sr.total - (1 / (n - 1)) * total - sr.total) ** 2
# +
# +        theta_results[sr.player_id] = (gamma / 2) * (1 / n - 2) * x
# +
# +    return theta_results
# +
# +
# +def ogl(survey_responses, total, big_n, n, q, gamma, method):
# +    results = dict()
# +
# +    theta_results = get_theta(survey_responses, total, n, gamma)
# +
# +    for sr in survey_responses:
# +        player_sum = sr.total
# +
# +        theta = theta_results[sr.player_id] if method <= 1 else 0
# +        ogl_results = n/big_n * ((q/n) * total + (gamma/2)*(n/(n-1))*(player_sum - ((1/n) * total))**2 - theta)
# +
# +        results[sr.player_id] = ogl_results - theta
# +
# +    return results



def write_session_dir(session_identifier):
    path = f'data/session_{session_identifier}/'

    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            print("Creation of the directory %s failed" % path)
            path = 'data/'
        else:
            print("Successfully created the directory %s " % path)

    return path


def skip_period(session, round_number):
    if session.config['skip_to_period'] > round_number:
        return True


class TimeFormatter:
    """This class accepts seconds and returns MM:SS.ss since first event"""
    def __init__(self, start):
        self.start = start

    def format(self, time):
        t = time - self.start
        minutes = math.floor(t // 60)
        seconds = t % 60
        return "{}:{}".format(minutes, seconds)

def unformat_time(time):
    breakdown = time.split(':')
    minutes = int(breakdown[0])
    seconds = float(breakdown[1])
    if minutes:
        seconds += minutes*60

    return seconds


def average_harvest():
    harvest_times = []
    file_name = "harvest_test.csv"

    f = open(file_name, 'r', newline='')
    harvest_start=None
    harvest_end=None
    for index, x in enumerate(f):
        columns = x.split(',')
        time = unformat_time(columns[22])

        harvest_status = int(columns[30])

        if index == 0:
            harvest_start = time

        if harvest_status != 4:
            continue

        if harvest_status == 4:
            harvest_end=time
            harvest_time = harvest_end-harvest_start
            harvest_times.append(harvest_time)
            harvest_start=harvest_end
        else:
            print('ERROR')

    # calculate averate
    total_time = 0
    total = len(harvest_times)
    for t in harvest_times:
        total_time += t

    print(f'AVERAGE HARVEST TIME {total_time/total}')
