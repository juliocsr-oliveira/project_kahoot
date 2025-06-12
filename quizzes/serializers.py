from rest_framework import serializers
from .models import Quiz, Pergunta, Resposta, Sala, Jogador, Resultado

# Serializers padrão
class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = '__all__'

class PerguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = '__all__'

class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = '__all__'

class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = '__all__'

class JogadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jogador
        fields = '__all__'

class ResultadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resultado
        fields = '__all__'

# NOVOS serializers usados só para criar quiz com perguntas aninhadas
class PerguntaInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pergunta
        fields = ['texto', 'tipo', 'dificuldade', 'pontuacao']

class QuizCreateSerializer(serializers.ModelSerializer):
    perguntas = PerguntaInlineSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['id', 'titulo', 'usuario', 'perguntas']

    def create(self, validated_data):
        perguntas_data = validated_data.pop('perguntas')
        quiz = Quiz.objects.create(**validated_data)
        for pergunta_data in perguntas_data:
            Pergunta.objects.create(quiz=quiz, **pergunta_data)
        return quiz
