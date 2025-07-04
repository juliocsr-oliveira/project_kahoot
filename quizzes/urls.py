from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, home, JogarQuizView, iniciar_quiz, sala_espera, QuizAnalysisView
from django.contrib.auth import views as auth_views
from account.views import UnifiedLoginView  

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('create/', QuizViewSet.as_view({'post': 'create'}), name='quiz_create'),
    path('play/<int:quiz_id>/', JogarQuizView.as_view(), name='quiz_play'),
    path('iniciar/<int:sala_id>/', iniciar_quiz, name='iniciar_quiz'),
    path('sala-espera/<int:sala_id>/', sala_espera, name='sala_espera'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('api/analise-dados/', QuizAnalysisView.as_view(), name='analise-dados'),
    path('quiz/<int:quiz_id>/dashboard/', QuizAnalysisView.as_view(), name='quiz_dashboard'),

]