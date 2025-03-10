from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, StdDev, F, Sum, Max, Min, Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Quiz, Pergunta, Resposta, RespostaUsuario, Sala, Jogador
from .serializers import QuizSerializer
import random
import string
import time


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        perguntas_data = request.data.get("perguntas", [])

        if len(perguntas_data) < 3:
            return Response(
                {"detail": "O quiz deve ter pelo menos 3 perguntas."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        response = super().create(request, *args, **kwargs)
        quiz_id = response.data.get("id")

        if quiz_id:
            quiz = Quiz.objects.get(id=quiz_id)

            for pergunta in perguntas_data:
                nova_pergunta = Pergunta.objects.create(
                    quiz=quiz,
                    texto=pergunta["texto"],
                    tipo=pergunta["tipo"],
                )

                for resposta in pergunta.get("respostas", []):
                    Resposta.objects.create(
                        pergunta=nova_pergunta,
                        texto=resposta["texto"],
                        correta=(str(resposta["correta"]) == "True")
                    )

            quiz.save()

        return response

class QuizAnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, quiz_id):
        try:
            quiz = get_object_or_404(Quiz, id=quiz_id)
            perguntas = Pergunta.objects.filter(quiz=quiz)
            respostas_usuario = RespostaUsuario.objects.filter(pergunta__in=perguntas)

            # Média de acertos por questão
            accuracy_per_question = perguntas.annotate(
                correct_count=Count('respostausuario', filter=Q(respostausuario__correta=True)),
                total_attempts=Count('respostausuario')
            ).values('id', 'texto', 'correct_count', 'total_attempts')

            # Tempo médio de resposta
            avg_response_time = respostas_usuario.values('pergunta_id').annotate(avg_time=Avg('tempo_resposta'))

            # Questão mais fácil e mais difícil
            most_correct = accuracy_per_question.order_by('-correct_count').first()
            least_correct = accuracy_per_question.order_by('correct_count').first()

            # Média e desvio padrão da pontuação
            avg_score = respostas_usuario.aggregate(Avg('pontuacao'))
            std_dev_score = respostas_usuario.aggregate(StdDev('pontuacao'))

            # Distribuição das respostas por alternativa
            answer_distribution = Resposta.objects.filter(pergunta__in=perguntas).annotate(
                selected_count=Count('respostausuario')
            ).values('pergunta_id', 'texto', 'selected_count')

            # Eficiência por jogador
            efficiency_ranking = respostas_usuario.values('jogador__nome').annotate(
                total_score=Sum('pontuacao'), avg_time=Avg('tempo_resposta')
            ).order_by('-total_score', 'avg_time')

            # Comparação de jogadores
            player_comparison = Jogador.objects.filter(sala__quiz=quiz).values('nome', 'pontuacao').order_by('-pontuacao')

            # Dificuldade progressiva (taxa de acerto ao longo do quiz)
            progressive_difficulty = respostas_usuario.values('pergunta__numero').annotate(
                correct_answers=Count('id', filter=Q(correta=True)),
                total_attempts=Count('id'),
                accuracy=F('correct_answers') * 100.0 / F('total_attempts')
            ).order_by('pergunta__numero')

            # Impacto do tempo limite
            time_limit_impact = respostas_usuario.values('pergunta_id').annotate(
                avg_time=Avg('tempo_resposta'),
                max_time=Max('tempo_resposta'),
                min_time=Min('tempo_resposta')
            )
            if request.user == quiz.criador:
                visualizar_dashboard = request.GET.get('ver_dashboard', 'false').lower() == 'true'
                if visualizar_dashboard:
                    return redirect(f'/dashboard/{quiz_id}')

            
            return Response({
                "accuracy_per_question": list(accuracy_per_question),
                "avg_response_time": list(avg_response_time),
                "most_correct": most_correct,
                "least_correct": least_correct,
                "avg_score": avg_score,
                "std_dev_score": std_dev_score,
                "answer_distribution": list(answer_distribution),
                "efficiency_ranking": list(efficiency_ranking),
                "player_comparison": list(player_comparison),
                "progressive_difficulty": list(progressive_difficulty),
                "time_limit_impact": list(time_limit_impact),
            })
        
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz não encontrado"}, status=404)

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
