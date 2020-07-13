# from delegated_punishment.models import Constants
from delegated_punishment.calculations.calculations import build_multinomial_input, prob_innocent_guilty


def test_prob_innocent_guilty(num_players, num_investigators):
    innocent_and_guilty = prob_innocent_guilty(num_players, num_investigators)

    print(f'Probability innocent and guilty calculations: {innocent_and_guilty}')


def test_build_multinomial_input(num_players, num_investigators, guilty_index, beta):

    multinomial_input = build_multinomial_input(num_players, num_investigators, guilty_index, beta)

    print(f'Multinomial input results: {multinomial_input}')

    print(f'Sum of inputs : {sum(multinomial_input)}')


def test_calculations():
    num_players = 6
    num_investigators = 2
    guilty_index = 2
    beta = .9

    test_prob_innocent_guilty(num_players, num_investigators)
    test_build_multinomial_input(num_players, num_investigators, guilty_index, beta)