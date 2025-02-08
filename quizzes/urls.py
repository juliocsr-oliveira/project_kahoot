from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, home, jogar_quiz, iniciar_quiz

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('', include(router.urls)),
    path('create/', QuizViewSet.as_view({'post': 'create'}), name='quiz_create'),
    path('play/<int:quiz_id>/', jogar_quiz, name='quiz_play'),
    path('iniciar/<int:sala_id>/', iniciar_quiz, name='iniciar_quiz'),
]