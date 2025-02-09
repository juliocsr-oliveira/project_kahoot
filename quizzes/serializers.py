from rest_framework import serializers
from .models import Quiz, Pergunta, Resposta

class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = '__all__'

class PerguntaSerializer(serializers.ModelSerializer):
    respostas = RespostaSerializer(many=True, read_only=True)

    class Meta:
        model = Pergunta
        fields = '__all__'

class QuizSerializer(serializers.ModelSerializer):
    perguntas = PerguntaSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = '__all__'

