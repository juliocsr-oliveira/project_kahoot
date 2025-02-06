from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from account.views import RegisterView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('galeria.urls')),
    path('api/account/', include('account.urls'))
]
