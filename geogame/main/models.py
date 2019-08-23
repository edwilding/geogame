import os
import random
import uuid

from django.contrib.postgres.search import SearchVectorField, SearchQuery, SearchVector
from django.conf import settings
from django.db import models, transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.shortcuts import reverse
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


from django_countries.fields import CountryField
from geopy import distance


class User(AbstractUser):
    first_name = models.CharField(_('first name'), max_length=50, blank=True, db_index=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True, db_index=True)
    email = models.EmailField(_('email address'), blank=False, null=False, db_index=True)
    api_key = models.CharField(_('google maps api key'), max_length=255, blank=True, db_index=True)

    def generate_new_game(self, country=None):
        game = Game.objects.create(
            start=timezone.now(),
            user=self,
            score=0,
            active=True,
            )
        qs = Coord.objects.all()
        if country:
            qs = qs.filter(country=country)
        coords = qs.order_by('?')[:5]
        for i, coord in enumerate(coords):
            round = GameRound.objects.create(
                game=game,
                coord=coord,
                order=i,
            )
            if i == 0:
                round_id = round.id
        return game.id, round_id

    def get_active_game(self):
        return Game.objects.filter(user=self, active=True).last()

    def deactive_games(self):
        return Game.objects.filter(user=self).update(active=False)


class Country(models.Model):
    country = models.CharField(_('Country'), max_length=255, null=False, blank=False)

    def __str__(self):
        return self.country


class Coord(models.Model):
    lng = models.CharField(_('longitude'), max_length=50, null=False, blank=False)
    lat = models.CharField(_('latitude'), max_length=50, null=False, blank=False)
    country = models.ForeignKey(Country, models.PROTECT,
                                related_name='coord_country',
                                null=False, blank=False)
    user = models.ForeignKey(User, models.PROTECT,
                             related_name='coord_user',
                             null=False, blank=False)


class Game(models.Model):
    start = models.DateTimeField()
    user = models.ForeignKey(User, models.PROTECT,
                             related_name='game_user',
                             null=False, blank=False)
    score = models.PositiveIntegerField()
    active = models.BooleanField()
    country = models.ForeignKey(Country, models.PROTECT,
                                related_name='game_country',
                                null=True, blank=True)

    def get_rounds(self):
        return GameRound.objects.filter(game=self)


class GameRound(models.Model):
    game = models.ForeignKey(Game, models.PROTECT,
                             related_name='round_game',
                             null=False, blank=False)
    coord = models.ForeignKey(Coord, models.CASCADE,
                              related_name='round_coord',
                              null=False, blank=False)
    order = models.IntegerField(_('round order'))
    guess_lat = models.CharField(_('latitude'), max_length=50, blank=True, null=True)
    guess_lng = models.CharField(_('longitude'), max_length=50, blank=True, null=True)

    def get_distance(self):
        if not self.guess_lat or not self.guess_lng:
            return 0
        actual_coord = (self.coord.lat, self.coord.lng,)
        guess_coord = (self.guess_lat, self.guess_lng,)
        return distance.distance(actual_coord, guess_coord).km
