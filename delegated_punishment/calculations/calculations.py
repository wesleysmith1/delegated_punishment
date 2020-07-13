def prob_innocent_guilty(num_players, num_investigators):
    return 1 / num_players - num_investigators / 20,  1 / num_players + num_investigators / 10


def build_multinomial_input(num_players, num_investigators, guilty_index, beta):
    """
    create array for multinomial input consisting of probabilities each player
    will be convicted as result of an intersection
    """

    innocent_prob, guilty_prob = prob_innocent_guilty(num_players, num_investigators)
    result = [0]

    for i in range(num_players):
        result.append(innocent_prob)

    result[guilty_index] = guilty_prob
    result[-1] = 1-beta

    return result

