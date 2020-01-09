# In my_app.pages
from django.http import HttpResponse
from django.core import serializers

from delegated_punishment.models import Player

def my_view(request):
    from django.core import serializers

    players = Player.objects.all()

    data = serializers.serialize('json', players)

    return HttpResponse(data, content_type='application/json')