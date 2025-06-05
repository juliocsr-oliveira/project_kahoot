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
    path('api/account/', include('account.urls')),
    path('api/', api_root),
    path('account/', include('django.contrib.auth.urls')),
    path('', home, name='home'),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/user/', CurrentUserView.as_view(), name='current_user'),
]

urlpatterns += [
    path('api/csrf-token/', get_csrf_token, name='csrf_token'),
]