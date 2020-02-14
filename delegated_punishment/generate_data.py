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
def generate_csv(group_players, round_number, session_id):

    print("HERE IS THE ROUND NUMBER {}".format(round_number))

    # todo: update this so that session start is not made here and only listened for since it should be the first gamedata item
    session_start = GameData.objects.first().event_time
    if not session_start:
        print("DATA NOT AVAILABLE")
        return

    tf = TimeFormatter(session_start)

    defend_tokens = init_defend_tokens()
    steal_tokens = init_steal_tokens()
    players = init_players(session_start)

    event_rows = init_main()

    # get data
    # game_data = GameData.objects.filter(session=session, group=group, round=round).order_by('event_time')
    game_data = GameData.objects.all().order_by('event_time')

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
                player['balance'] += Constants.civilian_income

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
                'punished': 0,
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
                    'punished': 0,
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
                'punished': 0,
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
                'punished': 0,
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
                'punished': 0,
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

            # update token data
            token_number = data['token_number']
            token_x1 = data['token_x']
            token_y1 = data['token_y']
            token_x2 = data['token_x2']
            token_y2 = data['token_y2']
            defend_map = data['map']

            defend_tokens[token_number] = format_defend_token(token_number, token_x1, token_y1, token_x2, token_y2, defend_map)
            event_defend_tokens = formatted_defend_tokens(defend_tokens)

            culprit_data = {
                'intersection_events': 'NA'
            }

            # check for intersections
            if data.get('intersections'):
                intersection_data = []

                # get victim so we can update the roi for each intersection
                victim_id = defend_map
                victim = players[victim_id]

                # update intersection event data
                for intersection in data['intersections']:

                    culprit_id = steal_token_id = intersection['culprit']
                    culprit = players[culprit_id]

                    decrease_roi(culprit, event_time)
                    increase_roi(victim, event_time)

                    investigation = True if intersection.get('guilty') else False

                    culprit_punished = 0

                    if investigation:
                        guilty_id = intersection['guilty']
                        guilty = players[guilty_id]
                        audit = intersection['audit']
                        reprimanded = 1 if intersection['officer_reprimand'] > 0 else 0
                        wrongful_conviction = 1 if intersection['wrongful_conviction'] else 0

                        # officer bonus
                        officer['balance'] += Constants.officer_intersection_payout

                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, guilty_id, audit, reprimanded)

                        # wrongful conviction
                        if wrongful_conviction:

                            # officer reprimand
                            officer['balance'] -= intersection['officer_reprimand']

                            guilty['balance'] -= Constants.civilian_conviction_amount

                            guilty_data = {
                                'event_type': event_type,
                                'last_updated': guilty['last_updated'],
                                'event_time': tf.format(event_time),
                                'balance': update_balance(guilty, event_time),
                                'roi': guilty['roi'],
                                'screen': guilty['screen'],
                                'steal_token': steal_tokens[guilty_id].format(),
                                'production_inputs': guilty['production_inputs'],
                                'punished': 1,
                                'defend_tokens': event_defend_tokens,
                                'intersection_events': i,
                            }
                            event_rows[guilty_id].append(guilty_data)

                        else:
                            # guilty culprit punishment
                            culprit_punished = 1
                            culprit['balance'] -= Constants.civilian_conviction_amount

                    else:
                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, 'NA', 0, 0)

                    # culprit location is implicitly reset here
                    steal_tokens[culprit_id].defend_token = token_number
                    culprit_data = {
                        'event_type': event_type,
                        'last_updated': culprit['last_updated'],
                        'event_time': tf.format(event_time),
                        'balance': culprit['balance'],
                        'roi': culprit['roi'],
                        'screen': 0,
                        'steal_token': steal_tokens[culprit_id].format(),  # todo: update steal token here
                        'production_inputs': culprit['production_inputs'],
                        'punished': culprit_punished,
                        'defend_tokens': event_defend_tokens,
                        'intersection_events': i,  # only add the culprit's intersection
                    }
                    event_rows[culprit_id].append(culprit_data)

                    # end of intersection code
                    intersection_data.append(i)

                # add formatted intersection data
                formatted_intersections = format_intersections(intersection_data)

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
                    'defend_tokens': event_defend_tokens,
                    'intersection_events': formatted_intersections,
                }
                event_rows[victim_id].append(victim_data)

                culprit_data['intersection_events'] = formatted_intersections

            culprit_data.update({
                'event_type': event_type,
                'last_updated': officer['last_updated'],
                'event_time': tf.format(event_time),
                'balance': officer['balance'],
                'roi': 0,
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': event_defend_tokens,
            })

            # update officer data
            event_rows[1].append(culprit_data)

        elif event_type == 'steal_token_update':
            culprit_id = data['culprit']
            culprit = players[culprit_id]

            token_x = data['token_x']
            token_y = data['token_y']
            steal_map = data['map']
            punished = 0

            victim_id = data['map']
            victim = players[victim_id]

            # changed if there is intersection
            defend_token_number = 'NA'
            # formatted_tokens
            event_defend_tokens = 'NA'
            formatted_intersection = 'NA'

            officer = players[1]

            if data.get('intersections'):

                event_defend_tokens = formatted_defend_tokens(defend_tokens)
                intersection = data['intersections'][0] # only one intersection possible
                defend_token_number = intersection['token_number'] #todo consider adding this to root of game data JSON
                steal_token_id = culprit_id  # same for first delegated_punishment experiment

                # check if there were investigation tokens
                investigation = True if intersection.get('guilty') else False

                if investigation:
                    guilty_id = intersection['guilty']

                    audit = intersection['audit']
                    reprimanded = 1 if intersection['officer_reprimand'] > 0 else 0

                    wrongful_conviction = 1 if intersection['wrongful_conviction'] else 0

                    # officer bonus
                    officer['balance'] += Constants.officer_intersection_payout

                    #todo clean this logic up
                    i = format_intersection(defend_token_number, culprit_id, steal_token_id, steal_map, 'NA' if guilty_id == 0 else guilty_id, audit, reprimanded)

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
                            'defend_tokens': event_defend_tokens,
                            'intersection_events': "[{}]".format(i)
                        }

                        event_rows[guilty_id].append(guilty_data)
                    else:
                        punished = 1
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
                "defend_tokens": event_defend_tokens,
                "intersection_events": formatted_intersection
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
                'punished': 0,
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
                'punished': punished,
                'defend_tokens': event_defend_tokens,
                'intersection_events': formatted_intersection
            }

            event_rows[culprit_id].append(culpit_data)

        elif event_type == 'period_start':
            session_start = event_time
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
                    'punished': 0,
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
                    'punished': 0,
                    'defend_tokens': 'NA' if i > 1 else formatted_defend_tokens(defend_tokens),
                    'intersection_events': 'NA'
                }
                event_rows[i].append(player_data)

        else:
            print('ERROR: EVENT TYPE NOT RECOGNIZED')

        # variables for csv
        import datetime, math

        session_date = datetime.datetime.today().strftime('%Y%m%d')
        # print out csv files
        for i in range(1, 6):
            role = 'Enforcer' if i == 1 else 'Civilian'
            start = math.floor(session_start)
            file_name = "Session_{}_{}_{}_{}_{}.csv".format(session_id, role, i, session_date, start)
            print(file_name)
            generate(i, event_rows[i], session_start, file_name)


def generate(pid, event_rows, start, file_name):
    f = open(file_name, 'a', newline='')  # todo make this append
    with f:
        writer = csv.writer(f)
        # write header
        writer.writerow(csv_header())
        for row in event_rows:
            writer.writerow(format_row(pid, row, start))


def csv_header():
    labels = [
        'Event Type',
        'Experiment Start',
        'Global Parameters',
        'Session ID',
        'PaymentScheme',
        'Income Distribution',
        'Player ID',
        'Player Role',
        'Period',
        'Current Time',
        'Balance',
        'ROI',
        'Screen',
        'Steal Token',
        'Production Inputs',
        'Punished',
        'Defend Tokens',
        'Intersection Events'
    ]
    return labels


def format_row(pid, r, start):
    return [
        r['event_type'],
        start,
        "[2,12, 10,1, 10, 300x300, 20, .1]",
        1,
        1,
        "[10,20,30,40,50]",
        pid,
        1 if pid > 1 else 0,
        1,
        r['event_time'],
        r['balance'],
        r['roi'],
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
        # x[i + 2] = {
        #     "number": i + 2,
        #     "x": 0,
        #     "y": 0,
        #     "map": "NA",
        #     "dropped": 1,
        #     "defend_token_id": 'NA'
        # }
    x[1] = 'NA'
    return x


def init_defend_tokens():
    x = {}
    for i in range(1, Constants.defend_token_total+1):
        x[i+1] = "[{}, {}, {}, {}, {}, {}, {}, {}]".format(i+1, 0, 0, 0, 0, 'NA', 1, 0)
        # x[i + 1] = {
        #     "number": i + 1,
        #     "x1": 0,
        #     "y1": 0,
        #     "x2": 0,
        #     "y2": 0,
        #     "map": "NA",
        #     "dropped": 1,
        #     "caught": 0,
        # }
    return x

def init_players(start):
    x = {}
    for i in range(1, 6):
        x[i] = {
            "last_updated": start,
            "player_id": i,
            "player_role": 0 if i == 1 else 1,
            "balance": 0,
            "screen": 1,
            "roi": 0,
            'production_inputs': 'NA' if i == 1 else '[0, 0, 0, 0]'
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
    p = [0, 0, 0, 0]
    for i in range(c):
        p[i] = 1
    return str(p)


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



