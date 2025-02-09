from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/account/', include('account.urls')),
    path('api/', include('quizzes.urls')),
    path('account/', include('django.contrib.auth.urls')),  # Adicione esta linha
]
