def prob_innocent_guilty(beta, a_max, num_civilians, num_investigators):
    # return 1 / num_players - num_investigators / 20,  1 / num_players + num_investigators / 10
    # return .225 - num_investigators * .0375, .225 + num_investigators * .1125

    innocent_prob = beta * (1 / (num_civilians - 1) - (1 / (num_civilians - 1)) * (num_investigators / a_max))

    guilty_prob = beta * (1 / (num_civilians - 1) + (
                (num_civilians - 2) / (num_civilians - 1) * (
                    num_investigators / a_max)))

    return innocent_prob, guilty_prob


def build_multinomial_input(num_civilians, num_investigators, culprit_index, victim_index, beta, a_max):
    """
    create array for multinomial input consisting of probabilities each player
    will be convicted as result of an intersection
    """

    innocent_prob, guilty_prob = prob_innocent_guilty(beta, a_max, num_civilians, num_investigators)
    result = [0]

    for i in range(num_civilians + 1):
        result.append(innocent_prob)

    result[culprit_index] = guilty_prob
    result[victim_index] = 0
    result[-1] = 1-beta

    return result

