from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User, Coord, Challenge, Game, GameRound

@admin.register(Coord)
class CoordAdmin(admin.ModelAdmin):
    list_display = 'id',


class CoordInline(admin.TabularInline):
    model = Coord
    fields = 'lat', 'lng', 'user',
    extra = 0


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'user',
    raw_id_fields = 'user',
    search_fields = 'name', 'user__display_name',
    ordering = 'id',
    inlines = [CoordInline]


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username',]

admin.site.register(User, CustomUserAdmin)
