import random
import csv


def generate_payouts(group):
    f = open("data/session_{}_results.csv".format(group.subsession.session_id), 'w', newline='')
    with f:
        writer = csv.writer(f)

        # header
        header = ['Name', 'Payment']
        writer.writerow(header)

        for player in group.get_players():
            # create row for participant and display the participant name
            if 'balances' in player.participant.vars.keys() and len(player.participant.vars['balances']) > 0:
                payout = random.choice(player.participant.vars['balances'])
                player.payout = payout
                player.save()
            else:
                payout = 0
            participant_data = [player.name, payout]
            writer.writerow(participant_data)