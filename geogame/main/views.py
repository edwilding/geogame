from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView
from django.db.models import Avg
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from braces import views

from geogame.main.models import (
    Game, GameRound, Coord, User, Challenge
)
from dal import autocomplete
from geogame.main.forms import GuessForm, ChallengeCoordFormSet, APIForm, ChallengeForm



class HomePageView(TemplateView):
    template_name = 'main/homepage.html'

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            if user.api_key:
                context['has_api_key'] = True
                try:
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
                except:
                    pass
            else:
                context['has_api_key'] = False
        return context


class ProfilePageView(views.LoginRequiredMixin, TemplateView):
    template_name = 'main/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        games = Game.objects.filter(user=user, active=False).order_by('-id')

        paginator = Paginator(games, 10)
        page = self.request.GET.get('played')
        try:
            played_paginator = paginator.page(page)
        except PageNotAnInteger:
            played_paginator = paginator.page(1)
        except EmptyPage:
            played_paginator = paginator.page(paginator.num_pages)
        context['played_is_paginated'] = played_paginator.has_other_pages()
        context['played_paginator'] = played_paginator

        challenges = Challenge.objects.filter(user=user).order_by('-id')
        paginator = Paginator(challenges, 10)
        page = self.request.GET.get('challenges')
        try:
            challenges_paginator = paginator.page(page)
        except PageNotAnInteger:
            challenges_paginator = paginator.page(1)
        except EmptyPage:
            challenges_paginator = paginator.page(paginator.num_pages)
        context['challenges_is_paginated'] = challenges_paginator.has_other_pages()
        context['challenges_paginator'] = challenges_paginator
        return context


class UpdateAPIView(views.UserPassesTestMixin, UpdateView):
    model = User
    form_class = APIForm
    template_name = 'main/api_form.html'
    raise_exception = True

    def test_func(self, user):
        user = get_object_or_404(User, pk=self.kwargs.get('pk', 0))
        return user == self.request.user

    def get_success_url(self):
        return reverse_lazy('profile')


class ChallengeCreateView(views.LoginRequiredMixin, CreateView):
    template_name = 'main/create_challenge_form.html'
    form_class = ChallengeForm

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        messages.success(self.request, 'Challenge Created Successfully, add some Co-ords')
        return redirect(reverse_lazy('game:edit-challenge', args=(self.object.id,)))


class EditChallengeView(views.UserPassesTestMixin, TemplateView):
    template_name = 'main/edit_challenge_form.html'

    def test_func(self, user):
        challenge = get_object_or_404(Challenge, pk=self.kwargs['pk'])
        return challenge.user == user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = get_object_or_404(Challenge, pk=self.kwargs['pk'])
        context['challenge'] = challenge
        context['formset'] = ChallengeCoordFormSet(queryset=Coord.objects.none())
        context['coords'] = Coord.objects.filter(challenge=challenge)
        #add form so users can edit the challenge name
        return context

    def post(self, *args, **kwargs):
        challenge = get_object_or_404(Challenge, pk=self.kwargs['pk'])
        formset = ChallengeCoordFormSet(self.request.POST)

        if formset.is_valid():
            for form in formset:
                obj = form.save(commit=False)
                obj.challenge = challenge
                obj.user = self.request.user
                obj.save()
                #XX prevent duplicates
            messages.success(self.request, 'Co-ords Updated Successfully')
            return redirect(reverse_lazy('game:edit-challenge', args=(challenge.id,)))
        messages.error(self.request, 'The form was invalid - something has gone wrong')
        return redirect(reverse_lazy('game:edit-challenge', args=(challenge.id,)))


class CoordDeleteView(views.UserPassesTestMixin, DeleteView):
    model = Coord

    def test_func(self, user):
        coord = self.get_object()
        return coord.user == user

    def get_success_url(self):
        challenge = self.object.challenge
        messages.success(self.request, 'Coord Removed Successfully')
        return reverse_lazy('game:edit-challenge',args=(challenge.id,))


class ChallengeListView(views.LoginRequiredMixin, ListView):
    template_name = 'main/challenge_list.html'
    context_object_name = 'challenges'
    paginate_by = 50

    def get_queryset(self):
        ids = Coord.objects.filter(challenge__isnull=False).\
            order_by().\
            values('challenge').\
            distinct()

        return Challenge.objects.filter(id__in=ids).order_by('id')


class NewGameView(views.LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = self.request.user
        user.deactive_games()
        if request.GET.get('challenge'):
            challenge = get_object_or_404(Challenge, pk=request.GET.get('challenge'))
            game_pk, round_pk = challenge.setup_challenge(user)
        else:
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


class RoundView(views.UserPassesTestMixin, UpdateView):
    model = GameRound
    form_class = GuessForm
    template_name = 'main/round.html'

    def test_func(self, *args, **kwargs):
        return self.request.user == get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0)).user

    def get_object(self):
        round_id = self.kwargs.get('round_pk', 0)
        return get_object_or_404(GameRound, pk=round_id)

    def get(self, *args, **kwargs):
        round_id = self.kwargs.get('round_pk', 0)
        round = get_object_or_404(GameRound, pk=round_id)

        if round.guess_lat:
            # user has already played this round, so something has gone wrong
            messages.warning(self.request, 'You have already played this round, something went wrong. Hit "Continue Last Game" to try again.')
            return redirect(reverse_lazy('home'))

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(RoundView, self).get_context_data(**kwargs)
        user = self.request.user
        round_id = self.kwargs.get('round_pk', 0)
        round = get_object_or_404(GameRound, pk=round_id)

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
        #add to the score and save against the game object, makes for easier score retrieval later
        self.object.game.score = self.object.game.score + self.object.result
        self.object.game.save()
        return redirect(
            reverse_lazy(
                'game:round-recap-view',
                kwargs={
                    'game_pk': self.object.game.pk,
                    'round_pk': self.object.pk,
                    }
                )
            )


class RemoveCoordView(View):
    def post(self, request, *args, **kwargs):
        round = get_object_or_404(GameRound, pk=self.kwargs.get('round_pk', 0))
        game = get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0))
        dodgy_coord = round.coord
        dodgy_coord.report()

        if game.challenge:
            round.score = 100
            round.guess_lat = 0
            round.guess_lng = 0
            round.save()
            next = round.order + 1
            next_round = GameRound.objects.filter(
                game=game,
                order=next,
            ).first()
            if next_round:
                return redirect(
                    reverse_lazy(
                        'game:round-view',
                        kwargs={
                            'game_pk': game.pk,
                            'round_pk': next_round.pk,
                        }
                    )
                )
            else:
                return redirect(
                    reverse_lazy(
                        'game:end-recap-view',
                        kwargs={
                            'game_pk': game.pk,
                        }
                    )
                )

        else:

            qs = Coord.objects.filter(reports=0)
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
                    'game_pk': game.pk,
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
        context['result'] = round.result

        next_round = GameRound.objects.filter(
            game=round.game,
            order=round.order + 1
        ).first()

        if not next_round:
            context['last_round'] = True
        else:
            context['next_round_id'] = next_round.id
        return context


class GameRecapView(views.UserPassesTestMixin, TemplateView):
    template_name = 'main/game_recap.html'

    def test_func(self, *args, **kwargs):
        return self.request.user == get_object_or_404(Game, pk=self.kwargs.get('game_pk', 0)).user

    def get_context_data(self, **kwargs):
        context = super(GameRecapView, self).get_context_data(**kwargs)
        game_id = self.kwargs.get('game_pk', 0)
        game = get_object_or_404(Game, pk=game_id)
        self.request.user.deactive_games()

        coord_results = []
        for round in GameRound.objects.filter(game=game).select_related('coord'):
            coord_results.append(
                [
                    [round.coord.lat, round.coord.lng],
                    [round.guess_lat if round.guess_lat else 0, round.guess_lng if round.guess_lng else 0]
                ]
            )

        context['results'] = coord_results
        context['total_score'] = game.score
        # not every game is part of a challenge, so keep this in a try
        try:
            context['all_average'] = game.challenge.average()
        except:
            pass
        return context