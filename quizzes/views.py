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
import random
import string
import time

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        quiz_id = response.data.get('id')
        if quiz_id:
            quiz = Quiz.objects.get(id=quiz_id)
            quiz.sala_ativa = Sala.objects.filter(quiz=quiz, ativa=True).first()
            quiz.save()
            try:
                quiz.clean()
            except ValidationError as e:
                quiz.delete()
                return Response({'detail': str(e)}, status=400)
        return response

def generate_room_code():
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Sala.objects.filter(codigo=codigo).exists():
            return codigo

def home(request):
    quizzes = Quiz.objects.all()
    for quiz in quizzes:
        quiz.sala_ativa = Sala.objects.filter(quiz=quiz, ativa=True).first()
    
    return render(request, 'quizzes/home.html', {'quizzes': quizzes})

def iniciar_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.user != quiz.criador:
        return Response({"error": "Apenas o criador do quiz pode iniciá-lo."}, status=403)
    sala, created = Sala.objects.get_or_create(quiz=quiz, ativa=True, defaults={'codigo': generate_room_code()})
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
        jogador = Jogador.objects.get(nome=request.user.username, sala=sala)
        pontuacao_total = 0
        for pergunta in quiz.pergunta_set.all():
            resposta_correta = pergunta.resposta_set.get(correta=True)
            inicio_tempo = time.time()
            resposta_usuario = request.POST.get(f'pergunta_{pergunta.id}')
            tempo_resposta = max(0.001, time.time() - inicio_tempo)  # Evita divisão por zero
            if resposta_usuario == resposta_correta.texto:
                pontuacao_pergunta = pergunta.pontuacao * (20 - min(20, tempo_resposta))
            else:
                pontuacao_pergunta = 0
            pontuacao_total += pontuacao_pergunta
        jogador.pontuacao = round(pontuacao_total, 3)  # Mantém a pontuação com até milésimos para desempate
        jogador.save()
        ranking = sorted(Jogador.objects.filter(sala=sala), key=lambda j: -j.pontuacao)
        return render(request, 'quizzes/resultado.html', {'ranking': ranking})

    return render(request, 'quizzes/quiz_play.html', {'quiz': quiz})

def sala_espera(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    jogadores = Jogador.objects.filter(sala=sala)

    if not sala.quiz or not sala.quiz.id:
        return Response({"error": "A sala não possui um quiz válido."}, status=400)

    if request.method == 'POST' and 'iniciar' in request.POST:
        if request.user != sala.quiz.criador:
            return Response({"error": "Apenas o criador do quiz pode iniciá-lo."}, status=403)
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
