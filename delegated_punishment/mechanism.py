import math
import csv
from decimal import Decimal

from delegated_punishment.helpers import format_template_numbers

# class MechanismProto:
#     def __init__(self, method):
#         self.method = method
#
#     def csv_header(self):
#         pass
#
#     def generate_csv(self):
#         pass
#
#     def start_vars(self):
#         pass
#
#     def result_vars(self):
#         pass

def format_decimal(d):
    return str(d).rstrip('0').rstrip('.')


class SurveyMechanism:

    def __init__(self):
        pass

    def csv_header(self, input_range):
        header = f"Player_Id, Participant_Id, Group_Id,"
        for i in range(1, input_range + 1):
            header += f"{i},"

        return [header]

    def generate_csv(self, survey_responses, input_range, filename):

        # csv file output per player
        f = open(filename, 'a', newline='')
        with f:
            writer = csv.writer(f)
            # write header

            writer.writerow(self.csv_header(input_range))

            for r in survey_responses:
                row = r.survey_row()
                writer.writerow(row)

    def start_vars(self, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            return dict(
                defend_token_total=total,
                defend_token_cost=format_decimal(cost),
                your_tax=format_decimal(response.tax),
            )

    def result_vars(self, group, player, response=None):
        if player.id_in_group == 1:
            return dict(
                defend_token_total=group.defend_token_total,
                fine_total=group.civilian_fine_total,
                bonus_total=group.officer_bonus_total,
            )
        else:
            if response is not None:
                # participant
                return dict(
                    # token
                    defend_token_total=group.defend_token_total,
                    defend_token_cost=format_decimal(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=format_decimal(Decimal(player.balance) - response.tax),
                    before_tax=format_decimal(player.balance),
                    your_tax=format_decimal(response.tax),
                )
            else:
                # this would be an error
                pass


class OglMechanism:

    def csv_header(self):
        header = f"Group_Id, Player_Id, Input, Created_At"

        return [header]

    def generate_csv(self, responses, filename):

        # csv file output per player
        f = open(filename, 'a', newline='')
        with f:
            # write header
            writer = csv.writer(f)

            writer.writerow(self.csv_header())

            for r in responses:
                row = r.gl_row()
                writer.writerow(row)

    def start_vars(self, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            return dict(
                defend_token_total=total,
                defend_token_cost=format_decimal(cost),
                your_tax=format_decimal(response.tax),
                your_tokens=response.total
            )

    def result_vars(self, group, player, response=None):
        if player.id_in_group == 1:
            return dict(
                defend_token_total=group.defend_token_total,
                fine_total=group.civilian_fine_total,
                bonus_total=group.officer_bonus_total,
            )
        else:
            if response is not None:
                # participant
                return dict(
                    # token
                    defend_token_total=group.defend_token_total,
                    defend_token_cost=format_decimal(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=format_decimal(Decimal(player.balance) - response.tax),
                    before_tax=player.balance,
                    your_tax=format_decimal(response.tax),
                    your_tokens=response.total,
                )
            else:
                # todo: there is an error here
                return None


class OtherMechanism:

    def csv_header(self):
        header = f"Group_Id, Player_Id, Input, Created_At"

        return [header]

    def generate_csv(self, responses, filename):
        # csv file output per player
        f = open(filename, 'a', newline='')
        with f:
            writer = csv.writer(f)
            # write header

            writer.writerow(self.csv_header())

            # determine if players received 50 grain
            for r in responses:
                row = r.gl_row()
                writer.writerow(row)

    def start_vars(self, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            result = dict(
                defend_token_total=str(total),
                defend_token_cost=format_decimal(cost),
                your_tax=format_decimal(response.tax),
            )

            if response.participant:
                result['rebate'] = response.rebate
                result['your_tokens'] = str(response.total)

            return result

    def result_vars(self, group, player, response=None):
        if player.id_in_group == 1:
            return dict(
                defend_token_total=group.defend_token_total,
                fine_total=group.civilian_fine_total,
                bonus_total=group.officer_bonus_total,
            )
        else:
            if response is not None:
                result = dict(
                    # token
                    defend_token_total=group.defend_token_total,
                    defend_token_cost=format_decimal(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=format_decimal(Decimal(player.balance) - response.tax + response.rebate),
                    before_tax=player.balance,
                    your_tax=format_decimal(response.tax),
                )

                if response.participant:
                    result['rebate'] = response.rebate
                    result['your_tokens'] = response.total

                return result
            else:
                # todo: this would be an error
                return None


class MechCSVBuilder:

    def __init__(self, method, responses, filename, input_range=None):
        self.method = method
        self.responses = responses
        self.filename = filename

        self.input_range = input_range

    def write(self):
        if self.method == 0:
            if self.input_range is None:
                raise ValueError('mechanism csv builder requires input_range for survey mechanism')

            SurveyMechanism().generate_csv(self.responses, self.filename, self.input_range)
        elif self.method == 1:
            OglMechanism().generate_csv(self.responses, self.filename)
        elif self.method > 1:
            OtherMechanism().generate_csv(self.responses, self.filename)
        else:
            # error
            print('there was an error')
