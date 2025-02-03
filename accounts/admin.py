from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CusterUserChangeForm
from .models import CustomUser

class CustomClassAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserCreationForm
    model = CustomUser
    list_display = ["email", "username",]


admin.site.register(CustomUser, CustomClassAdmin)

