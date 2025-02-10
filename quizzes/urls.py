from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, home, jogar_quiz, iniciar_quiz, api_home, api_root, sala_espera
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('api/home/', api_home, name='api_home'),
    path('create/', QuizViewSet.as_view({'post': 'create'}), name='quiz_create'),
    path('play/<int:quiz_id>/', jogar_quiz, name='quiz_play'),
    path('iniciar/<int:sala_id>/', iniciar_quiz, name='iniciar_quiz'),
    path('sala-espera/<int:sala_id>/', sala_espera, name='sala_espera'),
    path('login/', auth_views.LoginView.as_view(template_name='quizzes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # 🔥 Aqui estamos registrando a rota para buscar quizzes pelo ID
    path('quizzes/<int:pk>/', QuizViewSet.as_view({'get': 'retrieve'}), name='quiz-detail'),

    path('', include(router.urls)),  # Mantenha o router para outras rotas do ViewSet
]