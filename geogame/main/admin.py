from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User, Coord

@admin.register(Coord)
class CoordAdmin(admin.ModelAdmin):
    list_display = 'id', 'country',
    search_fields = 'country',


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ['email', 'username',]

admin.site.register(User, CustomUserAdmin)
