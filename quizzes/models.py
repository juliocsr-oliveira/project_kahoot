from django.db import models
from django.conf import settings

class Quiz(models.Model):
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Pergunta(models.Model):
    TIPOS_PERGUNTA = [
        ('MC', 'Múltipla Escolha'),
        ('VF', 'Verdadeiro ou Falso'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    texto = models.TextField()
    tipo = models.CharField(max_length=2, choices=TIPOS_PERGUNTA, default='MC')
    tempo_resposta = models.IntegerField(default=20)  # Tempo de resposta universal de 20 segundos
    pontuacao = models.IntegerField(default=10)  # Pontuação por resposta correta

    def __str__(self):
        return self.texto

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto = models.TextField()
    correta = models.BooleanField(default=False)

    def __str__(self):
        return self.texto

class Sala(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=10, unique=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)
    iniciada = models.BooleanField(default=False)  # Indica se a sala foi iniciada pelo host

    def __str__(self):
        return f"Sala {self.codigo} - {self.quiz.titulo}"

    def calcular_vencedor(self):
        jogadores = self.jogador_set.all()
        vencedor = max(jogadores, key=lambda jogador: jogador.pontuacao)
        return vencedor

    def calcular_ranking(self):
        jogadores = self.jogador_set.all().order_by('-pontuacao')
        return jogadores

class Jogador(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    pontuacao = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

class Resultado(models.Model):
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    pontuacao_total = models.IntegerField(default=0)
    data_jogo = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.jogador.nome} - {self.pontuacao_total} pontos"