# from delegated_punishment.models import Constants
from delegated_punishment.calculations.calculations import build_multinomial_input, prob_innocent_guilty


def test_prob_innocent_guilty(beta, a_max, num_civilians, num_investigators):
    innocent_and_guilty = prob_innocent_guilty(beta, a_max, num_civilians, num_investigators)

    print(f'Probability innocent and guilty calculations: {innocent_and_guilty}')


def test_build_multinomial_input(num_players, num_investigators, culprit_index, victim_index, beta, a_max):

    multinomial_input = build_multinomial_input(num_players, num_investigators, culprit_index, victim_index, beta, a_max)

    print(f'Multinomial input results: {multinomial_input}')

    print(f'Sum of inputs : {sum(multinomial_input)}')


def test_calculations():
    num_civilians = 5
    num_investigators = 2
    culprit_index = 2
    victim_index = 3
    beta = .9
    a_max = 6

    test_prob_innocent_guilty(beta, a_max, num_civilians, num_investigators)
    test_build_multinomial_input(num_civilians, num_investigators, culprit_index, victim_index, beta, a_max)