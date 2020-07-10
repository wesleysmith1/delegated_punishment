from decimal import Decimal


def probability_innocent(players, investigators):
    return 1 / players - investigators / 20


def probability_guilty(players, investigators):
    return 1 / players + investigators / 10


def calculate_gl_thetas(totals, q=8, n=8, N=8, gamma=9):
    results = dict()

    for (outer_index, outer_value) in enumerate(totals):
        temp_total = sum(totals)
        temp_total -= outer_value
        x = Decimal(0)

        for (inner_index, inner_value) in enumerate(totals):
            if inner_index == outer_index:
                continue

            ptotal = inner_value  # Decimal(sr2.total)
            # if player_id == sr2.player_id:
            #     ptotal += 1

            x = x + Decimal((ptotal - Decimal(1) / (n - Decimal(1)) * temp_total) ** 2)

        results[outer_index] = Decimal(gamma / 2) * Decimal(1 / (n - 2)) * x

    return results


def calculate_gl_costs(totals, q=8, n=8, N=8, gamma=9, player_ids=[], include_theta=True):
    """Theta is 0 for mgl methods"""

    if not player_ids:
        for (index, x) in enumerate(totals):
            player_ids.append(index)

    results = dict(zip(player_ids, totals))

    total = sum(totals)

    thetas = calculate_gl_thetas(totals, player_ids) if include_theta else None

    costs = dict()
    totals = dict()

    for ptotal, pid in zip(totals, player_ids):

        theta = thetas[pid] if thetas else 0
        result = Decimal((q / N) * total + (gamma / 2) * (
                    n / (n - 1)) * (ptotal - (1 / n) * total) ** 2) - theta

        costs[pid] = result

    return costs, totals


def check_ogl(totals, expected_output):
    results = calculate_gl_costs(totals)

    return len(expected_output) == len(results) and sorted(expected_output) == sorted(results)


def check_mgl(results, expected_output):
    results = calculate_gl_costs(results, beta=False)

    return len(expected_output) == len(results) and sorted(expected_output) == sorted(results)


def test_gl():
    totals_input = [1, 0, 0, 0, 0, 0, 0, 0]
    expected_output = [14.375, -0.625, -0.625, -0.625, -0.625, -0.625, -0.625, -0.625]
    assert check_ogl(totals_input, expected_output)