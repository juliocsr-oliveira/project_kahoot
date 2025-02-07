from rest_framework import serializers
from .models import Quiz, Pergunta, Resposta
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model

User = get_user_model()

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

