def probability_innocent(players, investigators):
    return 1 / players - investigators / 20


def probability_guilty(players, investigators):
    return 1 / players + investigators / 10
