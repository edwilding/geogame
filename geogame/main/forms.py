from django import forms
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.forms import widgets
from django.forms.utils import to_current_timezone
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import modelformset_factory

from geogame.main.models import (
    Coord, User, GameRound, Challenge
    )


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ('name',)


class GuessForm(forms.ModelForm):

    class Meta:
        model = GameRound
        fields = ('guess_lat', 'guess_lng',)
        widgets = {
            'guess_lat': forms.HiddenInput(),
            'guess_lng': forms.HiddenInput(),
            }

    def clean(self):
        cleaned_data = super(GuessForm, self).clean()
        lat = cleaned_data.get('lat')
        lng = cleaned_data.get('lng')


class APIForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('api_key', 'display_name',)


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = User
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'email')




ChallengeCoordFormSet = modelformset_factory(
    Coord,
    fields=('lat', 'lng',),
    extra=1,
)