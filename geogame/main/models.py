import os
import random
import uuid

from django.contrib.postgres.search import SearchVectorField, SearchQuery, SearchVector
from django.conf import settings
from django.db import models, transaction, IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.shortcuts import reverse
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from geopy import distance


class User(AbstractUser):
    first_name = models.CharField(_('first name'), max_length=50, blank=True, db_index=True)
    last_name = models.CharField(_('last name'), max_length=50, blank=True, db_index=True)
    email = models.EmailField(_('email address'), blank=False, null=False, db_index=True)
    api_key = models.CharField(_('google maps api key'), max_length=255, blank=True, db_index=True)
    display_name = models.CharField(_('display name'), max_length=25, blank=True, db_index=True)

    def generate_new_game(self):
        game = Game.objects.create(
            start=timezone.now(),
            user=self,
            score=0,
            active=True,
            )
        qs = Coord.objects.filter(reports=0)
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


class Challenge(models.Model):
    name = models.CharField(_('Challenge Name'), max_length=255, blank=True, db_index=True)
    average = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, models.PROTECT,
                             related_name='challenge_user',
                             null=False, blank=False)

    def update_average_score(self):
        average = GameRound.objects.filter(game__challenge=self).aggregate(Avg('result')).get('result__avg', 0)
        self.average = average
        self.save()
        return average

    def setup_challenge(self, user):
        rounds = Coord.objects.filter(challenge=self)
        game = Game.objects.create(
            challenge=self,
            start=timezone.now(),
            user=user,
            score=0,
            active=True,
        )
        for order, coord in enumerate(rounds):
            round = GameRound.objects.create(
                game=game,
                coord=coord,
                order=order
            )
            if order == 0:
                round_id = round.id
        return game.id, round_id


class Coord(models.Model):
    lng = models.CharField(_('longitude'), max_length=50, null=False, blank=False)
    lat = models.CharField(_('latitude'), max_length=50, null=False, blank=False)
    user = models.ForeignKey(User, models.PROTECT,
                             related_name='coord_user',
                             null=False, blank=False)
    reports = models.PositiveIntegerField(default=0)
    challenge = models.ForeignKey(Challenge, models.PROTECT,
                                  related_name='coord_challenge',
                                  null=True, blank=True)

    def report(self):
        self.reports = self.reports + 1
        self.save()


class Game(models.Model):
    challenge = models.ForeignKey(Challenge, models.PROTECT,
                             related_name='game_challenge',
                             null=True, blank=True)
    start = models.DateTimeField()
    user = models.ForeignKey(User, models.PROTECT,
                             related_name='game_user',
                             null=False, blank=False)
    score = models.PositiveIntegerField()
    active = models.BooleanField()

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
    result = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.guess_lat or not self.guess_lng:
            self.result = 0
        else:
            actual_coord = (self.coord.lat, self.coord.lng,)
            guess_coord = (self.guess_lat, self.guess_lng,)
            self.result = distance.distance(actual_coord, guess_coord).km * 1000
        super().save(*args, **kwargs)