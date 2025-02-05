from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Formulários personalizados para criação e edição de usuários
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    # Campos a serem exibidos na lista de usuários
    list_display = ('username', 'email', 'is_verified', 'is_staff', 'created_at')
    
    # Campos a serem usados nos filtros do admin
    list_filter = ('is_verified', 'is_staff')

    # Campos para pesquisa no admin
    search_fields = ('username', 'email')

    # Campos a serem exibidos no formulário de edição
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informações Pessoais', {'fields': ('telefone', 'data_nascimento')}),
        ('Permissões', {'fields': ('is_verified', 'is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('created_at',)}),
    )

    # Campos a serem exibidos no formulário de criação
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# Registrando o CustomUser no admin
admin.site.register(CustomUser, CustomUserAdmin)
