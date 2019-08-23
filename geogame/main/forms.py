from django import forms
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.forms import widgets
from django.forms.utils import to_current_timezone
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from geogame.main.models import (
    Coord, User, GameRound
    )

from dal import autocomplete
#from django_starfield import Stars


class CoordForm(forms.ModelForm):

    class Meta:
        model = Coord
        fields = ('lat', 'lng', 'country')
        widgets = {'country': autocomplete.ModelSelect2(url='game:country-autocomplete')}

    def clean(self):
        cleaned_data = super(CoordForm, self).clean()
        lat = cleaned_data.get('lat')
        lng = cleaned_data.get('lng')


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
        fields = ('api_key',)


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = User
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'email')
