from django.conf.urls import url
from django.contrib.auth.decorators import permission_required

from geogame.main.views import (
    RoundView, RoundRecapView, GameRecapView, NewGameView, ChallengeListView,
    EditChallengeView, RemoveCoordView, CoordDeleteView, ChallengeCreateView
)


urlpatterns = [
    url(r'^new-game/$', NewGameView.as_view(), name="new-game"),
    url(r'^round/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RoundView.as_view(), name="round-view"),
    url(r'^round-recap/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RoundRecapView.as_view(), name="round-recap-view"),
    url(r'^remove-coord/(?P<game_pk>\d+)/(?P<round_pk>\d+)/$', RemoveCoordView.as_view(), name="remove-coord"),
    url(r'^end-recap/(?P<game_pk>\d+)/$', GameRecapView.as_view(), name="end-recap-view"),
    url(r'^create-challenge/$', ChallengeCreateView.as_view(), name="create-challenge"),
    url(r'^list-challenge/$', ChallengeListView.as_view(), name="list-challenge"),
    url(r'^edit-challenge/(?P<pk>\d+)/$', EditChallengeView.as_view(), name="edit-challenge"),
    url(r'^coord/(?P<pk>\d+)/delete/$', CoordDeleteView.as_view(), name="coord-delete"),
]
