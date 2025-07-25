from django.contrib import admin
from django.urls import path, include
from quizzes.views import api_root, home
from django.middleware.csrf import get_token
from django.http import JsonResponse
from account.views import CurrentUserView

def get_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('account.urls')),
    path('api/', include('quizzes.urls')),
    
    path('api/', api_root),
    
    path('account/', include('django.contrib.auth.urls')),
    
    path('', home, name='home'),
    path('api/csrf-token/', get_csrf_token, name='csrf_token'),
]
