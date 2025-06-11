from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar novos usuários.

    Campos:
        - username: Nome de usuário do novo usuário.
        - email: Endereço de e-mail único do novo usuário.
        - password1: Senha do novo usuário.
        - password2: Confirmação da senha do novo usuário.

    Validações:
        - Verifica se as senhas fornecidas (password1 e password2) são iguais.

    Métodos:
        - validate: Valida os dados fornecidos, garantindo que as senhas sejam iguais.
        - create: Cria um novo usuário com os dados validados.
    """
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def validate(self, attrs):
        """
        Valida os dados fornecidos.

        Verifica se as senhas fornecidas (password1 e password2) são iguais.

        Retorno:
            - attrs: Dados validados.

        Exceções:
            - serializers.ValidationError: Caso as senhas não sejam iguais.
        """
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'A senha digitada não confere.'})
        return attrs

    def create(self, validated_data):
        """
        Cria um novo usuário com os dados validados.

        Retorno:
            - user: Instância do usuário criado.
        """
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = User(**validated_data)   
        user.set_password(password)
        user.save() 
        return user
    


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitar a redefinição de senha.

    Campos:
        - email: Endereço de e-mail do usuário que deseja redefinir a senha.

    Validações:
        - Verifica se o e-mail fornecido está associado a uma conta existente.

    Métodos:
        - validate_email: Valida se o e-mail está associado a um usuário.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Valida se o e-mail fornecido está associado a uma conta existente.

        Retorno:
            - value: E-mail validado.

        Exceções:
            - serializers.ValidationError: Caso o e-mail não esteja associado a nenhuma conta.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("O email não está associado a nenhuma conta.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar a redefinição de senha.

    Campos:
        - uidb64: ID do usuário codificado em base64.
        - token: Token de redefinição de senha.
        - new_password: Nova senha do usuário.

    Validações:
        - Verifica se o token e o UID fornecidos são válidos.

    Métodos:
        - validate: Valida o token e o UID fornecidos.
        - save: Atualiza a senha do usuário com a nova senha fornecida.
    """
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Valida o token e o UID fornecidos.

        Retorno:
            - attrs: Dados validados.

        Exceções:
            - serializers.ValidationError: Caso o token ou o UID sejam inválidos.
        """
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid token")

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError("Invalid token")

        return attrs

    def save(self):
        """
        Atualiza a senha do usuário com a nova senha fornecida.

        Retorno:
            - None
        """
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()

