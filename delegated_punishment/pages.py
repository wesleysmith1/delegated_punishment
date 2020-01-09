from ._builtin import Page, WaitPage
import json
from otree.api import Currency as c, currency_range
from .models import Constants, OfficerToken, Player
from random import random
from json import JSONEncoder

class Introduction(Page):
    #https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    def vars_for_template(self):
        pjson = dict()

        pjson['player'] = self.player.pk
        pjson['property'] = self.player.property
        pjson['x'] = self.player.x
        pjson['y'] = self.player.y

        print(pjson)
        vars_dict = dict()
        vars_dict['pjson'] = json.dumps(pjson)
        # if self.player.id_in_group == 1:
        #     officer_tokens = OfficerToken.objects.filter(group=self.group)
        #     vars['officer_tokens'] = officer_tokens
        return vars_dict

page_sequence = [Introduction]
