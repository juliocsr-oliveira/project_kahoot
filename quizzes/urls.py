from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, home, jogar_quiz, iniciar_quiz, sala_espera
from django.contrib.auth import views as auth_views
from account.views import UnifiedLoginView  # Importar a view do arquivo correto

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('create/', QuizViewSet.as_view({'post': 'create'}), name='quiz_create'),
    path('play/<int:quiz_id>/', jogar_quiz, name='quiz_play'),
    path('iniciar/<int:sala_id>/', iniciar_quiz, name='iniciar_quiz'),
    path('sala-espera/<int:sala_id>/', sala_espera, name='sala_espera'),
    path('login/', UnifiedLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]