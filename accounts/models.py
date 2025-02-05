from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    # Campos personalizados (opcional)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)

    # Resolvendo conflitos de acessores reversos
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',  # Nome único para o acessor reverso
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',  # Nome único para o acessor reverso
        related_query_name='user',
    )

    def __str__(self):
        return self.username

class CustomUser(AbstractUser):
    email = models.EmailField(unique = True)
    is_verified = models.BooleanField(default = False)
    created_at= models.DateTimeField(auto_now_add= True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email