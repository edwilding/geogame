from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy

from braces import views

from geogame.main.models import (
    Game, GameRound, Coord, User,  Country
)
from dal import autocomplete
from geogame.main.forms import GuessForm, CoordForm, APIForm


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Country.objects.none()

        qs = Country.objects.all().order_by('country')

        if self.q:
            qs = qs.filter(country__icontains=self.q)

        return qs


class HomePageView(TemplateView):
    template_name = 'main/homepage.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            if user.api_key:
                context['has_api_key'] = True
                game = Game.objects.filter(user=user, active=True)
                if game and game.exists():
                    game = game.first()
                    if not GameRound.objects.get(game=game, order=4).guess_lat:
                        context['existing_game'] = game
                        rounds = GameRound.objects.filter(game=game).order_by('order')
                        for round in rounds:
                            if not round.guess_lat or not round.guess_lng:
                                context['existing_round'] = round
                                break
            else:
                context['has_api_key'] = False
        return context


class ProfilePageView(views.LoginRequiredMixin, TemplateView):
    template_name = 'main/profile.html'


class UpdateAPIView(views.LoginRequiredMixin, UpdateView):
    model = User
    form_class = APIForm
    template_name = 'main/api_form.html'

    def get_success_url(self):
        return reverse_lazy('profile')


class ContributeView(views.LoginRequiredMixin, CreateView):
    model = Coord
    form_class = CoordForm
    template_name = 'main/contribute_form.html'

    def get_success_url(self):
        return reverse_lazy('game:contribute')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        messages.success(self.request, "Thank you so much for helping the site, you coordinates have been added.")
        return redirect(self.get_success_url())


class NewGameView(views.LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = self.request.user
        user.deactive_games()
        game_pk, round_pk = user.generate_new_game()

        return redirect(
            reverse_lazy(
                'game:round-view',
                kwargs={
                    'game_pk': game_pk,
                    'round_pk': round_pk,
                    }
                )
            )


class RoundView(views.LoginRequiredMixin, UpdateView):
    model = GameRound
    form_class = GuessForm
    template_name = 'main/round.html'

    def get_object(self):
        round_id = self.kwargs.get('round_pk', 0)
        return get_object_or_404(GameRound, pk=round_id)

    def get_context_data(self, **kwargs):
        context = super(RoundView, self).get_context_data(**kwargs)
        user = self.request.user
        round_id = self.kwargs.get('round_pk', 0)
        round = get_object_or_404(GameRound, pk=round_id)
        if round.guess_lat:
            #user has already played this round, so something has gone wrong
            messages.warning(self.request, 'You have already played this round, something went wrong. Hit "Continue Last Game" to try again.')
            return redirect(reverse_lazy('home'))

        context['api_key'] = user.api_key
        context['lat'] = round.coord.lat
        context['lng'] = round.coord.lng
        context['game_pk'] = round.game.pk
        context['round_pk'] = round.pk
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if not self.object.guess_lat or not self.object.guess_lng:
            self.object.guess_lat = 0
            self.object.guess_lng = 0
        self.object.save()
        round = self.get_object()
        return redirect(
            reverse_lazy(
                'game:round-recap-view',
                kwargs={
                    'game_pk': round.game.pk,
                    'round_pk': round.pk,
                    }
                )
            )

class RemoveCoordView(View):
    def post(self, request, *args, **kwargs):
        round = get_object_or_404(GameRound, pk=self.kwargs.get('round_pk', 0))
        game = get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0))
        qs = Coord.objects.all()
        if round.game.country:
            qs = qs.filter(country=round.game.country)
        coords = qs.order_by('?')[:5]

        current_coords = GameRound.objects.filter(game=game).exclude(id=round.id).values_list('coord__id', flat=True)
        for coord in coords:
            if coord.id not in current_coords:
                round.coord = coord
                round.save()
                break

        return redirect(
            reverse_lazy(
                'game:round-view',
                kwargs={
                    'game_pk': round.game.pk,
                    'round_pk': round.pk,
                    }
                )
            )



class RoundRecapView(views.UserPassesTestMixin, TemplateView):
    template_name = 'main/round_recap.html'

    def test_func(self, *args, **kwargs):
        return self.request.user == get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0)).user

    def get_context_data(self, **kwargs):
        context = super(RoundRecapView, self).get_context_data(**kwargs)
        user = self.request.user
        round_id = self.kwargs.get('round_pk', 0)
        round = get_object_or_404(GameRound, pk=round_id)

        context['api_key'] = user.api_key
        context['lat'] = round.coord.lat
        context['lng'] = round.coord.lng
        context['guess_lat'] = round.guess_lat
        context['guess_lng'] = round.guess_lng
        context['game_id'] = round.game.id
        context['distance'] = "{0:.3f}".format(round.get_distance())

        if round.order == 4:
            context['last_round'] = True
        else:
            next_round = GameRound.objects.get(
                game=round.game,
                order=round.order+1
                )
            context['next_round_id'] = next_round.id
        return context


class GameRecapView(views.UserPassesTestMixin, TemplateView):
    template_name = 'main/game_recap.html'

    def test_func(self, *args, **kwargs):
        return self.request.user == get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0)).user

    def get_context_data(self, **kwargs):
        context = super(GameRecapView, self).get_context_data(**kwargs)
        user = self.request.user
        game_id = self.kwargs.get('game_pk', 0)
        game = get_object_or_404(Game, pk=game_id)

        coord_results = []
        distance_total = 0
        for round in GameRound.objects.filter(game=game).select_related('coord'):
            coord_results.append(
                [
                    [round.coord.lat, round.coord.lng],
                    [round.guess_lat, round.guess_lng]
                ]
            )
            distance_total += round.get_distance()

        context['average_distance'] = "{0:.3f}".format(distance_total / 5)
        context['results'] = coord_results
        return context
