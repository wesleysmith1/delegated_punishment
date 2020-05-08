import math

from delegated_punishment.helpers import format_template_numbers

class SurveyMechanism:
    @classmethod
    def start_vars(cls, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            return dict(
                defend_token_total=total,
                defend_token_cost=format_template_numbers(cost),
                your_tax=format_template_numbers(response.tax)
            )


    @classmethod
    def result_vars(cls, group, player, response=None):
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
                    defend_token_cost=format_template_numbers(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=math.floor(player.balance - response.tax),
                    before_tax=math.floor(player.balance),
                    your_tax=format_template_numbers(response.tax),
                )
            else:
                # this would be an error
                pass

class OglMechanism:
    @classmethod
    def start_vars(cls, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            return dict(
                defend_token_total=total,
                defend_token_cost=format_template_numbers(cost),
                your_tax=format_template_numbers(response.tax),
                your_tokens=response.total
            )

    @classmethod
    def result_vars(cls, group, player, response=None):
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
                    defend_token_cost=format_template_numbers(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=math.floor(player.balance - response.tax),
                    before_tax=math.floor(player.balance),
                    your_tax=format_template_numbers(response.tax),
                    your_tokens=response.total
                )
            else:
                # todo: there is an error here
                return None


class OtherMechanism:
    @classmethod
    def start_vars(cls, id_in_group, total, cost, response=None):

        if id_in_group == 1:
            return dict(defend_token_total=total)
        else:
            result = dict(
                defend_token_total=total,
                defend_token_cost=format_template_numbers(cost),
                your_tax=format_template_numbers(response.tax),
            )

            if response.participant:
                result['your_tokens'] = response.total

    @classmethod
    def result_vars(cls, group, player, response=None):
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
                    defend_token_cost=format_template_numbers(group.defend_token_cost),
                    # your_tax

                    # results
                    balance=math.floor(player.balance - response.tax),
                    before_tax=math.floor(player.balance),
                    your_tax=format_template_numbers(response.tax),
                )

                if response.participant:
                    result['your_tokens'] = response.total

                return result
            else:
                # todo: this would be an error
                return None