import csv, math

from delegated_punishment.models import Constants, GameData

class TimeFormatter:
    """This class accepts seconds and returns MM:SS.ss since first event"""
    def __init__(self, start):
        self.start = start

    def format(self, time):
        t = time - self.start
        minutes = math.floor(t / 60)
        seconds = t % 60
        return "{}:{}".format(minutes, seconds)


# def generate_csv(session, group, round):
def generate_csv(group_id=9, round_number=9, session_id=9, session_start=Constants.epoch):

    # print("HERE IS THE ROUND NUMBER {}".format(round_number))

    tf = TimeFormatter(session_start)

    # session_start is assigned to this
    period_start = -1

    defend_tokens = init_defend_tokens()
    steal_tokens = init_steal_tokens()
    players = init_players(session_start)

    event_rows = init_main()

    # todo:
    # make a constants configuration to pass to functions

    # get data
    # game_data = GameData.objects.filter(session=session, group=group, round=round).order_by('event_time')
    game_data = GameData.objects.filter(s=session_id, g=group_id, round_number=round_number,).order_by('event_time')

    print("THERE ARE {} EVENTS FOR THIS PERIOD".format(len(game_data)))

    for event in game_data:
        # get JSON data
        data = event.jdata
        event_type = data['event_type']
        player_id = data['player']
        event_time = data['event_time']

        # determine event type
        if event_type == 'harvest':
            # update player into
            player = players[player_id]
            update_balance(player, event_time)

            # if harvest complete
            if data['production_inputs'] == 4:
                player['balance'] += data['harvest_income']

            player['production_inputs'] = format_production_inputs(data['production_inputs'])

            y = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(event_time),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': format_steal_token(player_id, 0, 0, 0, 'NA'),
                'production_inputs': player['production_inputs'],
                'punished': 'NA',
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            event_rows[data['player']].append(y)

            # reset harvest
            player['production_inputs'] = format_production_inputs(0)

        elif event_type == 'toggle':

            # update player into
            player = players[player_id]
            player['screen'] = format_screen(data['harvest_screen'])

            player['production_inputs'] = format_production_inputs(0)

            # update steal token
            steal_tokens[player_id].update(player_id, 0, 0, 0, 'NA')

            # check if there was a victim & update
            if data.get('victim'):
                # update player into
                victim_id = data['victim']
                victim = players[victim_id]
                increase_roi(victim, event_time)
                decrease_roi(player, event_time)

                victim_data = {
                    'event_type': event_type,
                    'last_updated': victim['last_updated'],
                    'event_time': tf.format(event_time),
                    'balance': victim['balance'],
                    'roi': victim['roi'],
                    'screen': victim['screen'],
                    'steal_token': steal_tokens[victim_id].format(),
                    'production_inputs': victim['production_inputs'],
                    'punished': 'NA',
                    'defend_tokens': 'NA',
                    'intersection_events': 'NA'
                }

                event_rows[victim_id].append(victim_data)

            civilian_data = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(event_time),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id].format(),
                'production_inputs': player['production_inputs'],
                'punished': 'NA',
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(civilian_data)

        elif event_type == 'steal_token_reset':
            # update player info
            player = players[player_id]

            update_balance(player, event_time)

            # update steal token
            steal_tokens[player_id].update(player_id, 0, 0, 0, 'NA')

            civilian_data = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(event_time),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id].format(),
                'production_inputs': player['production_inputs'],
                'punished': 'NA',
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(civilian_data)

        elif event_type == 'steal_token_drag':
            # update player info
            player = players[player_id]

            # update steal token
            steal_tokens[player_id].update(player_id, 0, 0, 'NA', 'NA')

            if data.get('victim'):
                victim_id = data['victim']
                victim = players[victim_id]

                # update roi
                increase_roi(victim, event_time)
                decrease_roi(player, event_time)

                # update victim data
                victim_data = {
                    'event_type': event_type,
                    'last_updated': victim['last_updated'],
                    'event_time': tf.format(event_time),
                    'balance': victim['balance'],
                    'roi': victim['roi'],
                    'screen': victim['screen'],
                    'steal_token': steal_tokens[victim_id].format(),
                    'production_inputs': victim['production_inputs'],
                    'punished': 0,
                    'defend_tokens': 'NA',
                    'intersection_events': 'NA',
                }
                event_rows[victim_id].append(victim_data)

            civilian_data = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(event_time),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id].format(),
                'production_inputs': player['production_inputs'],
                'punished': 'NA',
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(civilian_data)

        elif event_type == 'defend_token_reset':
            # get officer
            officer = players[1]

            update_balance(officer, event_time)

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, 0)

            officer_data = {
                'event_type': event_type,
                'last_updated': officer['last_updated'],
                'event_time': tf.format(event_time),
                'balance': officer['balance'],
                'roi': officer['roi'],
                'screen': 0,  # always 0 for officer
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': formatted_defend_tokens(defend_tokens),
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(officer_data)

        elif event_type == 'defend_token_drag':

            # get officer
            officer = players[1]

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, 'NA')

            officer_data = {
                'event_type': event_type,
                'last_updated': officer['last_updated'],
                'event_time': tf.format(event_time),
                'balance': officer['balance'],
                'roi': 0,
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': formatted_defend_tokens(defend_tokens),
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(officer_data)

        elif event_type == 'investigation_update':

            # get officer
            officer = players[1]

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, -1)
            event_defend_tokens = formatted_defend_tokens(defend_tokens)

            officer_data = {
                'event_type': event_type,
                'last_updated': officer['last_updated'],
                'event_time': tf.format(event_time),
                'balance': officer['balance'],
                'roi': 0,
                'screen': 0,  # always 0 for officer
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': event_defend_tokens,
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(officer_data)

        elif event_type == 'defend_token_update':

            # get officer
            officer = players[1]
            officer_reprimand_total = 0
            officer_data = {
                'intersection_events': 'NA'
            }

            # update token data
            token_number = data['token_number']
            token_x1 = data['token_x']
            token_y1 = data['token_y']
            token_x2 = data['token_x2']
            token_y2 = data['token_y2']
            defend_map = data['map']

            defend_tokens[token_number] = format_defend_token(token_number, token_x1, token_y1, token_x2, token_y2, defend_map)
            event_defend_tokens = formatted_defend_tokens(defend_tokens)

            # check for intersections
            if data.get('intersections'):
                intersection_data = []

                # get victim so we can update the roi for each intersection
                victim_id = defend_map
                victim = players[victim_id]

                updated_players = [victim_id]
                punished_players = []

                # update intersection event data
                for intersection in data['intersections']:

                    culprit_id = steal_token_id = intersection['culprit']
                    culprit = players[culprit_id]

                    # add culprit to updated_players list
                    if culprit_id not in updated_players:
                        updated_players.append(culprit_id)

                    decrease_roi(culprit, event_time)
                    increase_roi(victim, event_time)

                    investigation = True if intersection.get('guilty') else False

                    if investigation:
                        guilty_id = intersection['guilty']
                        guilty = players[guilty_id]

                        # add guilty
                        punished_players.append(guilty_id)

                        # add guilty to updated_players list
                        if guilty_id not in updated_players:
                            updated_players.append(guilty_id)

                        audit = intersection['audit']
                        reprimanded = 1 if intersection['officer_reprimand'] > 0 else 0
                        if reprimanded:
                            officer_reprimand_total += 1
                        wrongful_conviction = 1 if intersection['wrongful_conviction'] else 0

                        # officer bonus
                        officer['balance'] += intersection['officer_bonus']

                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, guilty_id, audit, reprimanded)

                        # wrongful conviction
                        if wrongful_conviction:

                            # officer reprimand
                            officer['balance'] -= intersection['officer_reprimand']

                            guilty['balance'] -= Constants.civilian_conviction_amount

                        else:
                            # guilty culprit punishment
                            culprit['balance'] -= Constants.civilian_conviction_amount

                    else:
                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, 'NA', 0, 0)

                    # culprit location is implicitly reset here
                    steal_tokens[culprit_id].defend_token = token_number

                    # print("CULPRIT_ID: {}".format(culprit_id))

                    # end of intersection code
                    intersection_data.append(i)

                # add formatted intersection data
                formatted_intersections = format_intersections(intersection_data)

                for pid in updated_players:
                    u_player = players[pid]
                    data = {
                        'event_type': event_type,
                        'last_updated': u_player['last_updated'],
                        'event_time': tf.format(event_time),
                        'balance': update_balance(u_player, event_time),
                        'roi': u_player['roi'],
                        'screen': 0,
                        'steal_token': steal_tokens[pid].format(),
                        'production_inputs': u_player['production_inputs'],
                        'punished': punished_players.count(pid),
                        'defend_tokens': 'NA',
                        'intersection_events': 'NA',
                    }
                    event_rows[pid].append(data)

                officer_data['intersection_events'] = formatted_intersections

            officer_data.update({
                'event_type': event_type,
                'last_updated': officer['last_updated'],
                'event_time': tf.format(event_time),
                'balance': officer['balance'],
                'roi': 0,
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': officer_reprimand_total,
                'defend_tokens': event_defend_tokens,
            })

            # update officer data
            event_rows[1].append(officer_data)

        elif event_type == 'steal_token_update':
            culprit_id = data['culprit']
            culprit = players[culprit_id]

            token_x = data['token_x']
            token_y = data['token_y']
            steal_map = data['map']
            culprit_punished = 'NA'

            victim_id = data['map']
            victim = players[victim_id]

            # changed if there is intersection
            defend_token_number = 'NA'
            # formatted_tokens
            event_defend_tokens = 'NA'
            formatted_intersection = 'NA'

            officer = players[1]
            officer_reprimand = 'NA'

            if data.get('intersections'):

                officer_reprimand = 0

                event_defend_tokens = formatted_defend_tokens(defend_tokens)
                intersection = data['intersections'][0]  # only one intersection possible
                defend_token_number = intersection['token_number']  # todo consider adding this to root of game data JSON
                steal_token_id = culprit_id  # same for first delegated_punishment experiment

                # check if there were investigation tokens
                investigation = True if intersection.get('guilty') else False

                if investigation:
                    guilty_id = intersection['guilty']

                    audit = intersection['audit']
                    reprimanded = 1 if intersection['officer_reprimand'] > 0 else 0
                    if reprimanded:
                        officer_reprimand = 1

                    wrongful_conviction = 1 if intersection['wrongful_conviction'] else 0

                    # officer bonus
                    officer['balance'] += intersection['officer_bonus']

                    #todo clean this logic up
                    i = format_intersection(
                        defend_token_number,
                        culprit_id,
                        steal_token_id,
                        steal_map,
                        'NA' if guilty_id == 0 else guilty_id,
                        audit,
                        reprimanded
                    )

                    # if wrongful conviction
                    if wrongful_conviction:
                        guilty = players[guilty_id]

                        # officer reprimand
                        officer['balance'] -= intersection['officer_reprimand']

                        guilty['balance'] -= Constants.civilian_conviction_amount

                        guilty_data = {
                            'event_type': event_type,
                            'last_updated': guilty['last_updated'],
                            'event_time': tf.format(data['event_time']),
                            'balance': update_balance(guilty, data['event_time']),  # get balance despite not having roi changed
                            'roi': guilty['roi'],
                            'screen': guilty['screen'],
                            'steal_token': steal_tokens[guilty_id].format(),
                            'production_inputs': guilty['production_inputs'],
                            'punished': 1,
                            'defend_tokens': 'NA',
                            'intersection_events': 'NA'
                        }
                        culprit_punished = 0
                        event_rows[guilty_id].append(guilty_data)
                    else:
                        culprit_punished = 1
                        culprit['balance'] -= Constants.civilian_conviction_amount

                else:
                    i = format_intersection(defend_token_number, culprit_id, steal_token_id, steal_map, 'NA', 0, 0)

                formatted_intersection = "[{}]".format(i)  # single intersection

            else:
                increase_roi(culprit, event_time)
                decrease_roi(victim, event_time)

            steal_tokens[culprit_id].update(player_id, token_x, token_y, steal_map, defend_token_number)

            victim_data = {
                'event_type': event_type,
                'last_updated': victim['last_updated'],
                "event_time": tf.format(data['event_time']),
                "balance": victim['balance'],
                "roi": victim['roi'],
                "screen": victim['screen'],
                "steal_token": steal_tokens[victim_id].format(),
                "production_inputs": victim['production_inputs'],
                "punished": 0,
                "defend_tokens": 'NA',
                "intersection_events": 'NA'
            }
            event_rows[victim_id].append(victim_data)

            officer_data = {
                'event_type': event_type,
                'last_updated': 'NA',
                'event_time': tf.format(data['event_time']),
                'balance': officer['balance'],
                'roi': officer['roi'],
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': officer_reprimand,
                'defend_tokens': formatted_defend_tokens(defend_tokens),  # todo this is not elegant
                'intersection_events': formatted_intersection
            }
            # add officer data
            event_rows[1].append(officer_data)

            steal_tokens[culprit_id].defend_token = defend_token_number
            culpit_data = {
                'event_type': event_type,
                'last_updated': culprit['last_updated'],
                'event_time': tf.format(event_time),
                'balance': culprit['balance'],
                'roi': culprit['roi'],
                'screen': 0,
                'steal_token': steal_tokens[culprit_id].format(),
                'production_inputs': culprit['production_inputs'],
                'punished': culprit_punished,
                'defend_tokens': 'NA',
                'intersection_events': formatted_intersection
            }

            event_rows[culprit_id].append(culpit_data)

        elif event_type == 'period_start':
            period_start = event_time
            tf = TimeFormatter(period_start)
            for i in range(1, 6):

                player_data = {
                    'event_type': event_type,
                    'last_updated': 'NA',
                    'event_time': tf.format(event_time),
                    'balance': players[i]['balance'],
                    'roi': players[i]['roi'],
                    'screen': players[i]['screen'],
                    'steal_token': steal_tokens[i].format(),
                    'production_inputs': players[i]['production_inputs'],
                    'punished': 'NA',
                    'defend_tokens': 'NA' if i > 1 else formatted_defend_tokens(defend_tokens),
                    'intersection_events': 'NA'
                }
                event_rows[i].append(player_data)

        elif event_type == 'period_end':
            for i in range(1, 6):
                update_balance(players[i], event_time)
                # add end time to csv

                player_data = {
                    'event_type': event_type,
                    'last_updated': 'NA',
                    'event_time': tf.format(event_time),
                    'balance': players[i]['balance'],
                    'roi': players[i]['roi'],
                    'screen': players[i]['screen'],
                    'steal_token': steal_tokens[i].format(),
                    'production_inputs': players[i]['production_inputs'],
                    'punished': 'NA',
                    'defend_tokens': 'NA' if i > 1 else formatted_defend_tokens(defend_tokens),
                    'intersection_events': 'NA'
                }
                event_rows[i].append(player_data)

            # any events after this should not be included
            break

        else:
            print('ERROR: EVENT TYPE NOT RECOGNIZED')

    # variables for csv
    import datetime, math

    session_date = datetime.datetime.today().strftime('%Y%m%d')
    # print out csv files
    for i in range(1, 6):
        start = math.floor(session_start)
        file_name = "data/Session_{}_Group_{}_Player_{}_{}_{}.csv".format(session_id, 1, i, session_date, start)
        generate(i, event_rows[i], file_name, period_start, round_number, session_id, group_id)


def generate(pid, event_rows, file_name, period_start, period, session_id, group_id):
    f = open(file_name, 'a', newline='')  # todo make this append
    with f:
        writer = csv.writer(f)
        # write header
        if period == 1:
            writer.writerow(csv_header())
        for row in event_rows:
            writer.writerow(format_row(pid, row, period_start, period, session_id, group_id))


def csv_header():
    labels = [
        'EventType',
        'Session_ID',
        'Session_GlobalParameters',
        'Group_ID',
        'Group_BonusAmount',
        'Group_IncomeDistribution',
        'Player_ID',
        'Player_Role',
        'Period_ID',
        'Period_CurrentTime',
        'ROI',
        'Player_Balance',
        'Player_Screen',
        'Player_StealToken',
        'Player_ProductionInputs',
        'Player_Punished',
        'Player_DefendTokens',
        'Group_PunishmentEvents',
    ]
    return labels


def format_row(pid, r, period_start, period, session_id, group_id):
    # innocent_prob = 1 / 3 - num_investigators / 30
    # guilty_prob = 1 / 3 + 2 * num_investigators / 30
    return [
        r['event_type'],
        session_id,
        [
            Constants.civilian_steal_rate,
            Constants.civilian_conviction_amount,
            Constants.defend_token_total,
            "a min 1 , a max 10",
            Constants.defend_token_size,
            Constants.civilian_map_size,
            Constants.officer_reprimand_amount,
            Constants.officer_review_probability,
        ],  # session global params?
        group_id,
        Constants.officer_incomes[0][period % 4 - 1],
        Constants.civilian_incomes_one[0] if period < 5 else Constants.civilian_incomes_two[0],  # group_income_distribution
        pid,
        1 if pid > 1 else 0,
        period,
        r['event_time'],
        r['roi'],
        r['balance'],
        r['screen'],
        r['steal_token'],
        r['production_inputs'],
        r['punished'],
        r['defend_tokens'],
        r['intersection_events']
    ]

class StealToken:
    def __init__(self, number):
        self.number = number
        self.x = 0
        self.y = 0
        self.map = 0
        self.defend_token = 'NA'

    def update(self, number, x, y, smap, defend_token):
        self.number = number
        self.x = x
        self.y = y
        self.map = smap
        self.defend_token = defend_token

    def format(self):
        return "[{}, {}, {}, {}, {}]".format(self.number, self.x, self.y, self.map, self.defend_token)


def init_steal_tokens():
    x = {}
    for i in range(2,6):
        x[i] = StealToken(i)
    x[1] = 'NA'
    return x


def init_defend_tokens():
    x = {}
    for i in range(1, Constants.defend_token_total+1):
        x[i] = "[{}, {}, {}, {}, {}, {}, {}, {}]".format(i, 0, 0, 0, 0, 'NA', 1, 0)
    return x


def init_players(start):
    x = {}
    for i in range(1, 6):
        x[i] = {
            "last_updated": start,
            "player_id": i,
            "player_role": 0 if i == 1 else 1,
            "balance": 200,  # todo make this refer to constants
            "screen": 0 if i == 1 else 1,
            "roi": 0,
            'production_inputs': 'NA' if i == 1 else 0
        }

    return x


def init_main():
    """one dict for each player"""
    x = {}
    for i in range(1,6):
        x[i] = []
    return x


def update_balance(player, event_time):
    # return calculated balance
    if player['roi'] == 0:
        return player['balance']
    elif not event_time or not player['last_updated']:
        print('ERROR: START DATE OR END DATE MISSING WHEN CALCULATING')
        return -99
    else:
        return player['balance'] + player['roi'] * (event_time - player['last_updated'])


def increase_roi(player, event_time):
    player['balance'] = update_balance(player, event_time)
    player['last_updated'] = event_time
    player['roi'] += Constants.civilian_steal_rate


def decrease_roi(player, event_time):
    player['balance'] = update_balance(player, event_time)
    player['last_updated'] = event_time
    player['roi'] -= Constants.civilian_steal_rate


def format_production_inputs(c):
    # p = [0, 0, 0, 0]
    # for i in range(c):
    #     p[i] = 1
    # return str(p)
    return c


def format_steal_token(token_number, x, y, steal_map, defend_token):
    return "[{}, {}, {}, {}, {}]".format(token_number, x, y, steal_map, defend_token)


def format_defend_token(token_number, x1, y1, x2, y2, defend_map):
    return "[{}, {}, {}, {}, {}, {}]".format(token_number, x1, y1, x2, y2, defend_map)


def formatted_defend_tokens(defend_dict):
    result = "["

    for num, value in defend_dict.items():
        result += value
        # add separator
        if num != 9:
            result += ';'

    result += "]"
    return result


def format_intersection(token_number, culprit_id, steal_token_id, intersection_map, guilty_player_id, audit, reprimanded):
    """ for now culprit_id and steal_token_id are the same """
    return "[{}, {}, {}, {}, {}, {}, {}]".format(token_number, culprit_id, steal_token_id, intersection_map, guilty_player_id, audit, reprimanded)


def format_intersections(i_list):
    result = "[" + ";".join(i_list) + "]"
    return result


def format_screen(s):
    if s:
        return 1
    else:
        return 0



