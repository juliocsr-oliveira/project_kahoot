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
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Quiz, Pergunta, Resposta
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Quiz, Pergunta, Resposta
from .serializers import QuizSerializer

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
                tipo = pergunta["tipo"]
                respostas = pergunta.get("respostas", [])

                # Validação do número de respostas
                if tipo == "trueFalse" and len(respostas) != 2:
                    return Response(
                        {"detail": f"Pergunta '{pergunta['texto']}' deve ter 2 respostas para 'trueFalse'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if tipo == "MC" and len(respostas) != 4:
                    return Response(
                        {"detail": f"Pergunta '{pergunta['texto']}' deve ter 4 respostas para 'MC'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                nova_pergunta = Pergunta.objects.create(
                    quiz=quiz,
                    texto=pergunta["texto"],
                    tipo=tipo,
                )

                for resposta in respostas:
                    Resposta.objects.create(
                        pergunta=nova_pergunta,
                        texto=resposta["texto"],
                        correta=str(resposta["correta"]).lower() == "true"
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

            accuracy_per_question = perguntas.annotate(
                correct_count=Count('respostausuario', filter=Q(respostausuario__correta=True)),
                total_attempts=Count('respostausuario')
            ).values('id', 'texto', 'correct_count', 'total_attempts')

            avg_response_time = respostas_usuario.values('pergunta_id').annotate(avg_time=Avg('tempo_resposta'))

            most_correct = accuracy_per_question.order_by('-correct_count').first()
            least_correct = accuracy_per_question.order_by('correct_count').first()

            avg_score = respostas_usuario.aggregate(Avg('pontuacao'))
            std_dev_score = respostas_usuario.aggregate(StdDev('pontuacao'))

            answer_distribution = Resposta.objects.filter(pergunta__in=perguntas).annotate(
                selected_count=Count('respostausuario')
            ).values('pergunta_id', 'texto', 'selected_count')

            efficiency_ranking = respostas_usuario.values('jogador__nome').annotate(
                total_score=Sum('pontuacao'), avg_time=Avg('tempo_resposta')
            ).order_by('-total_score', 'avg_time')

            player_comparison = Jogador.objects.filter(sala__quiz=quiz).values('nome', 'pontuacao').order_by('-pontuacao')

            progressive_difficulty = respostas_usuario.values('pergunta__numero').annotate(
                correct_answers=Count('id', filter=Q(correta=True)),
                total_attempts=Count('id'),
                accuracy=F('correct_answers') * 100.0 / F('total_attempts')
            ).order_by('pergunta__numero')

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


class JogarQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        perguntas = Pergunta.objects.filter(quiz=quiz)

        perguntas_serializadas = []
        for pergunta in perguntas:
            respostas = Resposta.objects.filter(pergunta=pergunta)
            perguntas_serializadas.append({
                "text": pergunta.texto,
                "options": [r.texto for r in respostas],
                "correctAnswer": respostas.filter(correta=True).first().texto if respostas.filter(correta=True).exists() else None,
                "points": pergunta.pontuacao,
            })

        return Response({
            "titulo": quiz.titulo,
            "questions": perguntas_serializadas
        })



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


@login_required
def quiz_create_page(request):
    return render(request, 'quizzes/quiz_create.html')


@api_view(['GET'])
def api_root(request):
    return Response({
        "home": "http://127.0.0.1:8000/",
        "api_home": "http://127.0.0.1:8000/api/home/",
        "create_quiz": "http://127.0.0.1:8000/create/",
        "play_quiz": "http://127.0.0.1:8000/play/<int:quiz_id>/",
        "iniciar_quiz": "http://127.0.0.1:8000/iniciar/<int:sala_id>/",
    })
