from django.conf.urls import url
from django.contrib.auth.decorators import permission_required

from geogame.main.views import (
    RoundView, RoundRecapView, GameRecapView, NewGameView,
    ContributeView, CountryAutocomplete, RemoveCoordView
)


urlpatterns = [
    url(r'^new-game/$', NewGameView.as_view(), name="new-game"),
    url(r'^round/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RoundView.as_view(), name="round-view"),
    url(r'^round-recap/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RoundRecapView.as_view(), name="round-recap-view"),
    url(r'^remove-coord/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RemoveCoordView.as_view(), name="remove-coord"),
    url(r'^end-recap/(?P<game_pk>\d+)/$', GameRecapView.as_view(), name="end-recap-view"),
    url(r'^contribute/$', ContributeView.as_view(), name="contribute"),
    url(r'^country-autocomplete/$', CountryAutocomplete.as_view(), name='country-autocomplete',
    ),
]
