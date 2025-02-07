from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizViewSet, home

router = DefaultRouter()
router.register(r'quizzes', QuizViewSet)

urlpatterns = [
    path('', home, name='home'),
    path('', include(router.urls)),
    path('create/', QuizViewSet.as_view({'post': 'create'}), name='quiz_create'),
    path('play/<int:quiz_id>/', QuizViewSet.as_view({'get': 'retrieve'}), name='quiz_play'),
]