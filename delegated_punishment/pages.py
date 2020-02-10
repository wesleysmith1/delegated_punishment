from ._builtin import Page, WaitPage
import json
from otree.api import Currency as c, currency_range
from .models import Constants, DefendToken, Player
from random import random
from json import JSONEncoder


class Introduction(Page):
    timeout_seconds = 240
    #https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    def vars_for_template(self):

        # print('THE PAGE WAS FUCKING REFRESHED: ' + str(self.player.harvest_screen))

        # pp = Player.objects.get(pk=1)
        # import pdb;
        # pdb.set_trace()

        #  todo: we need to query player here since a blank model is being created instad
        #   of pulling from db. This is required to load data from the database.

        pjson = dict()
        pjson['player'] = self.player.pk
        pjson['map'] = self.player.map
        pjson['x'] = self.player.x
        pjson['y'] = self.player.y
        pjson['harvest_screen'] = self.player.harvest_screen

        vars_dict = dict()
        vars_dict['pjson'] = json.dumps(pjson)
        vars_dict['rand'] = str(random() * 1000) #todo: remove
        if self.player.id_in_group == 1:
            officer_tokens = DefendToken.objects.filter(group=self.group)
            # for o in officer_tokens:
                # print("TOKEN {} - MAP  {} - X {:6.2f} - Y {:6.2f}".format(o.number, str(o.map), o.x, o.y)) #todo: these values are correct. Why are they not getting passed down to client?
            results = [obj.to_dict() for obj in officer_tokens]
            vars_dict['dtokens'] = json.dumps(results)

        return vars_dict

class TestWaitPage(WaitPage):
    pass


page_sequence = [TestWaitPage, Introduction]
