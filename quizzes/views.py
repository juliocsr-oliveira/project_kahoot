from django.shortcuts import render, redirect
from rest_framework import viewsets
from .models import Quiz, Sala, Jogador
from .serializers import QuizSerializer
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

def home(request):
    quizzes = Quiz.objects.all()
    return render(request, 'quizzes/home.html', {'quizzes': quizzes})

@login_required
def iniciar_quiz(request, sala_id):
    sala = Sala.objects.get(id=sala_id)
    sala.iniciada = True
    sala.save()
    return redirect('jogar_quiz', quiz_id=sala.quiz.id)

@login_required
def jogar_quiz(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    sala = Sala.objects.get(quiz=quiz, ativa=True)
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
                pontuacao += pergunta.pontuacao  # Use a pontuação definida pelo usuário
        jogador.pontuacao = pontuacao
        jogador.save()

        # Calcular o ranking
        ranking = sala.calcular_ranking()

        return render(request, 'quizzes/resultado.html', {'ranking': ranking})

    return render(request, 'quizzes/quiz_play.html', {'quiz': quiz})

@api_view(['GET'])
def api_home(request):
    data = {"mensage": "API funcionando!"}
    return Response(data)
def home_view(request):
    return render(request, 'quizzes/template/quizzes/home.html')