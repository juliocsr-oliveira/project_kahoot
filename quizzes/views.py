from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets
from .models import Quiz, Sala, Jogador
from .serializers import QuizSerializer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.exceptions import ValidationError
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect


class CustomLoginView(auth_views.LoginView):
    template_name = 'quizzes/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        return redirect('token_obtain_pair')

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        quiz = self.get_object()
        try:
            quiz.clean()
        except ValidationError as e:
            quiz.delete()
            return Response({'detail': str(e)}, status=400)
        return response

def home(request):
    quizzes = Quiz.objects.all()
    return render(request, 'quizzes/home.html', {'quizzes': quizzes})

def iniciar_quiz(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    sala.iniciada = True
    sala.save()
    return redirect('jogar_quiz', quiz_id=sala.quiz.id)

def jogar_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    sala = Sala.objects.filter(quiz=quiz, ativa=True).first()

    if not sala:
        return Response({"error": "Nenhuma sala ativa encontrada para este quiz."}, status=404)

    if not sala.iniciada:
        return render(request, 'quizzes/aguardando_inicio.html', {'sala': sala})

    if request.method == 'POST':
        # Lógica para calcular a pontuação do jogador
        jogador = Jogador.objects.get(nome=request.user.username, sala=sala)
        pontuacao = 0
        for pergunta in quiz.pergunta_set.all():
            resposta_correta = pergunta.resposta_set.get(correta=True)
            resposta_usuario = request.POST.get(f'pergunta_{pergunta.id}')
            if resposta_usuario == resposta_correta.texto:
                pontuacao += pergunta.pontuacao  # Usa a pontuação definida pelo usuário
        jogador.pontuacao = pontuacao
        jogador.save()

        # Calcular o ranking
        ranking = sala.calcular_ranking()

        return render(request, 'quizzes/resultado.html', {'ranking': ranking})

    return render(request, 'quizzes/quiz_play.html', {'quiz': quiz})

def sala_espera(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    jogadores = Jogador.objects.filter(sala=sala)

    if not sala.quiz or not sala.quiz.id:
        return Response({"error": "A sala não possui um quiz válido."}, status=400)

    if request.method == 'POST' and 'iniciar' in request.POST:
        sala.iniciada = True
        sala.save()
        return redirect('jogar_quiz', quiz_id=sala.quiz.id)

    return render(request, 'quizzes/sala_espera.html', {'sala': sala, 'jogadores': jogadores})

@api_view(['GET'])
def api_home(request):
    return Response({"message": "API está funcionando"})

@api_view(['GET'])
def api_root(request):
    return Response({
        "home": "http://127.0.0.1:8000/",
        "api_home": "http://127.0.0.1:8000/api/home/",
        "create_quiz": "http://127.0.0.1:8000/create/",
        "play_quiz": "http://127.0.0.1:8000/play/<int:quiz_id>/",
        "iniciar_quiz": "http://127.0.0.1:8000/iniciar/<int:sala_id>/",
    })
