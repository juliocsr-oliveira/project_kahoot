from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, login
from django.shortcuts import redirect, render
from .serializers import UserSerializer, RegisterSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.deprecation import MiddlewareMixin
from rest_framework import permissions

User = get_user_model()

class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Retorna os dados do usuário autenticado.

        Retorno:
            - JsonResponse: Dados do usuário autenticado.
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    
class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Middleware para desabilitar a verificação de CSRF em rotas que começam com '/api/'.

    Métodos:
        - process_request: Desabilita a verificação de CSRF para requisições que correspondem ao prefixo '/api/'.
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)


@csrf_exempt
def teste_csrf(request):
    """
    Endpoint de teste para verificar se a verificação de CSRF foi desabilitada.

    Retorno:
        - JsonResponse: Retorna {"PASSOU": True}.
    """
    return JsonResponse({"PASSOU": True})


logger = logging.getLogger(__name__)

User = get_user_model()
@method_decorator(csrf_exempt, name='dispatch')

class UnifiedLoginView(APIView):
    """
    APIView para gerenciar o login de usuários.

    Métodos:
        - get: Renderiza a página de login.
        - post: Autentica o usuário e retorna tokens JWT ou redireciona para a página inicial.

    Permissões:
        - Permite acesso a qualquer usuário (autenticado ou não).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Renderiza a página de login.

        Retorno:
            - Template HTML da página de login.
        """
        return render(request, 'login.html')

    def post(self, request, *args, **kwargs):
        """
        Autentica o usuário com base nas credenciais fornecidas.

        Processamento:
            - Verifica se o username e password foram fornecidos.
            - Autentica o usuário.
            - Retorna tokens JWT para requisições JSON ou redireciona para a página inicial.

        Retorno:
            - 200 OK: Login bem-sucedido.
            - 400 Bad Request: Credenciais ausentes.
            - 401 Unauthorized: Credenciais inválidas.
        """
        username = request.data.get('username') or request.POST.get('username')
        password = request.data.get('password') or request.POST.get('password')

        if not username or not password:
            error_response = {"error": "Usuário e senha são obrigatórios."}
            if request.content_type.startswith("application/json"):
                return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
            return render(request, 'login.html', {"error": error_response["error"]})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if request.content_type.startswith("application/json"):
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                login(request, user)
                return redirect('/')
        else:
            error_response = {"error": "Credenciais inválidas"}
            if request.content_type.startswith("application/json"):
                return Response(error_response, status=status.HTTP_401_UNAUTHORIZED)
            return render(request, 'login.html', {"error": error_response["error"]})


class RegisterView(APIView):
    """
    APIView para gerenciar o registro de novos usuários.

    Métodos:
        - get: Renderiza a página de registro.
        - post: Registra um novo usuário e redireciona para a página de login.

    Permissões:
        - Permite acesso a qualquer usuário (autenticado ou não).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Renderiza a página de registro.

        Retorno:
            - Template HTML da página de registro.
        """
        return render(request, 'register.html')

    def post(self, request):
        """
        Registra um novo usuário com base nos dados fornecidos.

        Processamento:
            - Valida os dados fornecidos.
            - Cria um novo usuário.
            - Redireciona para a página de login.

        Retorno:
            - 302 Found: Redireciona para a página de login após o registro bem-sucedido.
            - 400 Bad Request: Dados inválidos.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"success": "Conta criada com sucesso!"}, status=status.HTTP_201_CREATED)
        else: return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    APIView para gerenciar o logout de usuários.

    Métodos:
        - post: Invalida o token de refresh e redireciona para a página inicial.

    Permissões:
        - Apenas usuários autenticados podem acessar esta view.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Realiza o logout do usuário.

        Processamento:
            - Invalida o token de refresh fornecido.
            - Redireciona para a página inicial.

        Retorno:
            - 302 Found: Redireciona para a página inicial após o logout.
            - 400 Bad Request: Caso ocorra um erro ao invalidar o token.
        """
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return redirect('/')
        except Exception as e:
            return Response({"error": "Erro ao realizar logout."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    APIView para gerenciar solicitações de redefinição de senha.

    Métodos:
        - get: Renderiza a página de solicitação de redefinição de senha.
        - post: Envia um e-mail com o link para redefinição de senha.

    Permissões:
        - Permite acesso a qualquer usuário (autenticado ou não).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Renderiza a página de solicitação de redefinição de senha.

        Retorno:
            - Template HTML da página de solicitação de redefinição de senha.
        """
        return render(request, 'account/password_reset.html')

    def post(self, request):
        """
        Envia um e-mail com o link para redefinição de senha.

        Processamento:
            - Verifica se o e-mail fornecido está associado a um usuário.
            - Gera um token de redefinição de senha.
            - Envia o link de redefinição de senha por e-mail.

        Retorno:
            - 302 Found: Redireciona para a página de login após o envio do e-mail.
        """
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
        return redirect('/login/')


class PasswordResetConfirmView(APIView):
    """
    APIView para confirmar a redefinição de senha.

    Métodos:
        - get: Renderiza a página de confirmação de redefinição de senha.
        - post: Redefine a senha do usuário.

    Permissões:
        - Permite acesso a qualquer usuário (autenticado ou não).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        """
        Renderiza a página de confirmação de redefinição de senha.

        Retorno:
            - Template HTML da página de confirmação de redefinição de senha.
        """
        return render(request, 'account/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})

    def post(self, request, uidb64, token):
        """
        Redefine a senha do usuário.

        Processamento:
            - Valida os dados fornecidos.
            - Atualiza a senha do usuário.

        Retorno:
            - 200 OK: Senha redefinida com sucesso.
            - 400 Bad Request: Dados inválidos.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Sua senha foi resetada com sucesso!'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
