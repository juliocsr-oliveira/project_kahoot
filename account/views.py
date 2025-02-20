from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import redirect, render
from .serializers import RegisterSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
import logging


logger = logging.getLogger(__name__)

User = get_user_model()

class UnifiedLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return render(request, 'quizzes/login.html')
    
    def post(self, request, *args, **kwargs):
        # Se a requisição for JSON (para API), faz login com JWT
        if request.content_type == "application/json":
            username = request.data.get('username')
            password = request.data.get('password')

            user = authenticate(username=username, password=password)
            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Credenciais inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        # Caso contrário, processa login tradicional via formulário
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')  # Redireciona para a home se login for bem-sucedido
            else:
                return JsonResponse({"error": "Credenciais inválidas"}, status=401)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return render(request, 'quizzes/register.html')

    def post(self, request):
        print("dados", request.data)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return redirect('quizzes/login') 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return redirect('/')  # Redireciona para a home após logout
        except Exception as e:
            return Response({"error": "Erro ao realizar logout."}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return render(request, 'quizzes/password_reset.html')

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
            send_mail(
                'Redefinição de Senha',
                f'Use o link abaixo para redefinir sua senha: {reset_url}',
                'no-reply@yourdomain.com',
                [user.email],
                fail_silently=False,
            )
        return redirect('/login/')  # Redireciona para a página de login após redefinição de senha

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        return render(request, 'quizzes/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password has been reset'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
