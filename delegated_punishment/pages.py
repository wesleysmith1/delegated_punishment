from ._builtin import Page, WaitPage
import json
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
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

        vars_dict = dict()
        vars_dict['pjson'] = json.dumps(pjson)
        vars_dict['rand'] = str(random() * 1000) #todo: remove
        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)
            # for o in officer_tokens:
                # print("TOKEN {} - PROPERTY  {} - X {:6.2f} - Y {:6.2f}".format(o.number, str(o.property), o.x, o.y)) #todo: these values are correct. Why are they not getting passed down to client?
            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

            # import pdb;
            # pdb.set_trace()
        return vars_dict


page_sequence = [Introduction]
