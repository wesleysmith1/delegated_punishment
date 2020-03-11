import random
import csv
import math
from delegated_punishment.helpers import write_session_dir


def get_path(group):
    if 'session_identifier' in group.subsession.session.config:
        path = write_session_dir(group.subsession.session.config['session_identifier'])
    else:
        path = 'data/'
    return path


def split_list(a_list):
    half = len(a_list)//2
    return a_list[:half], a_list[half:]


def calculate_payout(balance, showup_payment, endowment):
    payout = balance + endowment
    if balance < 0:
        payout = showup_payment
    else:
        balance += showup_payment

    return math.ceil(payout)

def grain_to_dollars(group, grain):
    return grain * group.subsession.session.config['grain_conversion']



def generate_payouts(group):
    path = get_path(group)

    endowment = group.subsession.session.config['participant_endowment']
    showup_payment = group.subsession.session.config['showup_payment']

    for player in group.get_players():
        # create row for participant and display the participant name
        participant_balances_recorded = len(player.participant.vars['balances'])
        if 'balances' in player.participant.vars.keys() and participant_balances_recorded == 8:

            participant_balances = player.participant.vars['balances']

            balance = random.choice(participant_balances)

            payout = calculate_payout(balance, showup_payment, endowment)

        elif participant_balances_recorded == 1:
            balance = player.participant.vars['balances'][0]
            payout = calculate_payout(balance, showup_payment, endowment)
        else:
            payout = -1

        player.payout = payout
        player.save()


def generate_survey_csv(group):
    print('GENERATING SURVEY CSV')
    path = get_path(group)
    session_id = group.subsession.session_id
    session_start = math.floor(group.session.vars['session_start'])
    session_date = group.session.vars['session_date']
    file_name = "{}results{}__{}_{}.csv".format(path, session_id, session_date, session_start)

    f = open(file_name, 'w', newline='')
    with f:
        writer = csv.writer(f)
        header = ['participant', 'payout', 'race_ethnicity', 'gender', 'strategy', 'feedback']
        writer.writerow(header)

        for p in group.get_players():
            survey_row = [p.participant.id_in_session, p.payout, p.race_ethnicity, p.gender, p.strategy, p.feedback]
            writer.writerow(survey_row)

