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
def generate_csv():
    # start data
    frame_size = .25
    session_start = GameData.objects.first().event_time
    tf = TimeFormatter(session_start)

    defend_tokens = init_defend_tokens()
    punishment_events = init_punishment_events()
    steal_tokens = init_steal_tokens()
    players = init_players(session_start)

    event_rows = init_main()

    # get data
    # game_data = GameData.objects.filter(session=session, group=group, round=round).order_by('event_time')
    game_data = GameData.objects.all().order_by('event_time')

    for event in game_data:
        # get JSON data
        data = event.jdata  # todo bud
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
                'event_time': tf.format(data['event_time']),
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

        elif event_type == 'toggle':

            # update player into
            player = players[player_id]
            player['screen'] = format_screen(data['harvest_screen'])

            player['production_inputs'] = format_production_inputs(0) # todo: make this singular 'production_input'

            # update steal token
            steal_tokens[player_id] = format_steal_token(player_id, 0, 0, 0, 'NA')

            # check if there was a victim & update
            if data.get('victim'):
                # update player into
                victim_id = data['victim']
                victim = players[victim_id]
                increase_roi(victim, event_time)
                decrease_roi(player, event_time)

                z = {
                    'event_type': event_type,
                    'last_updated': victim['last_updated'],
                    'event_time': tf.format(data['event_time']),
                    'balance': victim['balance'],
                    'roi': victim['roi'],
                    'screen': victim['screen'],
                    'steal_token': steal_tokens[victim_id],
                    'production_inputs': victim['production_inputs'],
                    'punished': 0,
                    'defend_tokens': 'NA',
                    'intersection_events': 'NA'
                }

                event_rows[victim_id].append(z)

            y = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id],
                'production_inputs': player['production_inputs'],
                'punished': 0,
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(y)

        elif event_type == 'steal_token_reset':
            # update player info
            player = players[player_id]

            update_balance(player, event_time)

            # update steal token
            steal_tokens[player_id] = format_steal_token(player_id, 0, 0, 0, 'NA')

            y = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id],
                'production_inputs': player['production_inputs'],
                'punished': 0,
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(y)

        elif event_type == 'steal_token_drag':  # token don't always include player_roi or victim_info for this event
            # update player info
            player = players[player_id]

            # update steal token
            steal_tokens[player_id] = format_steal_token(player_id, 0, 0, 'NA', 'NA')

            if data.get('victim'):
                victim_id = data['victim']
                victim = players[victim_id]

                # update roi
                increase_roi(victim, event_time)
                decrease_roi(player, event_time)

                # update victim data
                v = {
                    'event_type': event_type,
                    'last_updated': victim['last_updated'],
                    'event_time': tf.format(data['event_time']),
                    'balance': victim['balance'],
                    'roi': victim['roi'],
                    'screen': victim['screen'],
                    'steal_token': steal_tokens[victim_id],  # fix this warning
                    'production_inputs': victim['production_inputs'],
                    'punished': 0,
                    'defend_tokens': 'NA',
                    'intersection_events': 'NA',
                }
                event_rows[victim_id].append(v)

            y = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': player['screen'],
                'steal_token': steal_tokens[player_id],
                'production_inputs': player['production_inputs'],
                'punished': 0,
                'defend_tokens': 'NA',
                'intersection_events': 'NA'
            }
            # add civilian row
            event_rows[player_id].append(y)

        elif event_type == 'defend_token_reset':
            # get officer
            player = players[1]

            update_balance(player, event_time)

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, 0)

            t = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': player['roi'],
                'screen': 0,  # always 0 for officer
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': formatted_defend_tokens(defend_tokens),
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(t)

        elif event_type == 'defend_token_drag':

            # get officer
            player = players[1]

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, 'NA')

            t = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': 0,
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': formatted_defend_tokens(defend_tokens),
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(t)

        elif event_type == 'investigation_update':

            # get officer
            player = players[1]

            # reset defend token
            token_number = data['token_number']
            defend_tokens[token_number] = format_defend_token(token_number, 0, 0, 0, 0, -1)
            event_defend_tokens = formatted_defend_tokens(defend_tokens)

            t = {
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': 0,
                'screen': 0,  # always 0 for officer
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': event_defend_tokens,
                'intersection_events': 'NA'
            }
            # add officer row
            event_rows[1].append(t)

        elif event_type == 'defend_token_update':

            # get officer
            player = players[1]

            # update token data
            token_number = data['token_number']
            token_x1 = data['token_x']
            token_y1 = data['token_y']
            token_x2 = data['token_x2']
            token_y2 = data['token_y2']
            defend_map = data['map']

            defend_tokens[token_number] = format_defend_token(token_number, token_x1, token_y1, token_x2, token_y2, defend_map)
            event_defend_tokens = formatted_defend_tokens(defend_tokens)

            #culprit object
            d = {
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

                        player['balance'] -= Constants.officer_reprimand_amount

                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, guilty_id, audit, reprimanded)

                        # wrongful conviction
                        if wrongful_conviction:

                            # officer reprimand
                            player['balance'] -= Constants.officer_reprimand_amount

                            guilty['balance'] -= Constants.civilian_conviction_amount
                            update_balance(guilty, event_time)

                            w = {
                                'event_type': event_type,
                                'last_updated': guilty['last_updated'],
                                'event_time': tf.format(data['event_time']),
                                'balance': guilty['balance'],
                                'roi': guilty['roi'],
                                'screen': guilty['screen'],
                                'steal_token': steal_tokens[guilty_id],
                                'production_inputs': guilty['production_inputs'],
                                'punished': 1,
                                'defend_tokens': event_defend_tokens,
                                'intersection_events': i,
                            }
                            event_rows[guilty_id].append(w)

                        else:
                            # guilty culprit punishment
                            culprit_punished = 1
                            culprit['balance'] -= Constants.civilian_conviction_amount

                    else:
                        i = format_intersection(token_number, culprit_id, steal_token_id, defend_map, 0, 0, 0)

                    c = {
                        'event_type': event_type,
                        'last_updated': culprit['last_updated'],
                        'event_time': tf.format(data['event_time']),
                        'balance': culprit['balance'],
                        'roi': culprit['roi'],
                        'screen': 0,
                        'steal_token': steal_tokens[culprit_id],
                        'production_inputs': culprit['production_inputs'],
                        'punished': culprit_punished,
                        'defend_tokens': event_defend_tokens,
                        'intersection_events': i,  # only add the culprit's intersection
                    }
                    event_rows[culprit_id].append(c)

                    # end of intersection code
                    intersection_data.append(i)

                # add formatted intersection data
                formatted_intersections = format_intersections(intersection_data)

                # update victim data
                v = {
                    'event_type': event_type,
                    'last_updated': victim['last_updated'],
                    'event_time': tf.format(data['event_time']),
                    'balance': victim['balance'],
                    'roi': victim['roi'],
                    'screen': victim['screen'],
                    'steal_token': steal_tokens[victim_id],
                    'production_inputs': victim['production_inputs'],
                    'punished': 0,
                    'defend_tokens': event_defend_tokens,
                    'intersection_events': formatted_intersections,
                }
                event_rows[victim_id].append(v)

                d['intersection_events'] = formatted_intersections

            d.update({
                'event_type': event_type,
                'last_updated': player['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': player['balance'],
                'roi': 0,
                'screen': 0,
                'steal_token': 'NA',
                'production_inputs': 'NA',
                'punished': 'NA',
                'defend_tokens': event_defend_tokens,
            })

            # update officer data
            event_rows[1].append(d)

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
            steal_tokens[culprit_id] = format_steal_token(player_id, token_x, token_y, steal_map, defend_token_number)
            event_defend_tokens = 'NA'
            formatted_intersection = 'NA'

            if data.get('intersection'):
                event_defend_tokens = formatted_defend_tokens(defend_tokens)
                intersection = data['intersection']
                audit = intersection['audit']
                defend_token_number = intersection['token_number']
                steal_token_id = culprit_id  # same for first delegated_punishment experiment
                reprimanded = 1 if intersection['reprimanded'] > 0 else 0
                guilty_id = intersection['guilty']
                wrongful_conviction = 1 if intersection['wrongful_conviction'] else 0

                i = format_intersection(defend_token_number, culprit_id, steal_token_id, steal_map, guilty_id, audit, reprimanded)
                formatted_intersection = "[{}]".format(i) # single intersection

                # if wrongful conviction
                if wrongful_conviction:
                    guilty = players[guilty_id]

                    guilty['balance'] -= Constants.civilian_conviction_amount

                    w = {
                        'event_type': event_type,
                        'last_updated': guilty['last_updated'],
                        'event_time': tf.format(data['event_time']),
                        'balance': guilty['balance'],
                        'roi': guilty['roi'],
                        'screen': guilty['screen'],
                        'steal_token': steal_tokens[guilty_id],
                        'production_inputs': guilty['production_inputs'],
                        'punished': 1,
                        'defend_tokens': event_defend_tokens,
                        'intersection_events': formatted_intersection
                    }

                    event_rows[guilty_id].append(w)
                else:
                    punished = 1
            else:
                increase_roi(culprit, event_time)
                decrease_roi(victim, event_time)

            # victim dict
            v = {
                'event_type': event_type,
                'last_updated': victim['last_updated'],
                "event_time": tf.format(data['event_time']),
                "balance": victim['balance'],
                "roi": victim['roi'],
                "screen": victim['screen'],
                "steal_token": steal_tokens[victim_id],
                "production_inputs": victim['production_inputs'],
                "punished": 0,
                "defend_tokens": event_defend_tokens,
                "intersection_events": formatted_intersection
            }
            event_rows[victim_id].append(v)

            s = {
                'event_type': event_type,
                'last_updated': culprit['last_updated'],
                'event_time': tf.format(data['event_time']),
                'balance': culprit['balance'],
                'roi': culprit['roi'],
                'screen': 0,
                'steal_token': steal_tokens[culprit_id],
                'production_inputs': 'NA',
                'punished': punished,
                'defend_tokens': event_defend_tokens,
                'intersection_events': formatted_intersection
            }

            event_rows[culprit_id].append(s)
        else:
            print('ERROR: EVENT TYPE NOT RECOGNIZED')

        # print out csv files
        for i in range(1, 6):
            generate(i, event_rows[i])


def generate(pid, event_rows):
    f = open('delegated_punishment_{}.csv'.format(pid), 'w', newline='')
    with f:
        writer = csv.writer(f)
        # write header
        writer.writerow(csv_header())
        for row in event_rows:
            writer.writerow(format_row(row))


def csv_header():
    labels = [
        'Event Type',
        'Event Time',
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


def format_row(r):
    return [
        r['event_type'],
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


def init_defend_tokens():
    x = {}
    for i in range(9):
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


def init_steal_tokens():
    x = {}
    for i in range(4):
        x[i+2] = "[{}, {}, {}, {}, {}]".format(i+2, 0, 0, 'NA', 0, 'NA')
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


def init_punishment_events():
    x = {}
    for i in range(9):
        x[i + 1] = "NA"
    return x


def init_punishment_event(culprit, guilty, reprimand):
    x = {}
    for i in range(9):
        x[i + 1] = {
            "culprit_player_id": culprit,
            "steal_token_id": culprit,
            "guilty_player_id": guilty,
            "reprimanded": reprimand,
        }
    return x


def init_players(start):
    x = {}
    for i in range(5):
        x[i + 1] = {
            "last_updated": start,
            "player_id": i + 1,
            "player_role": 1,
            "balance": 0,
            "screen": 1,
            "roi": 0,
            'production_inputs': '[0,0,0,0]'
        }
    # officer
    x[1]["player_role"] = 0
    return x


def init_main():
    """one dict for each player"""
    x = {}
    for i in range(5):
        x[i + 1] = []
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



