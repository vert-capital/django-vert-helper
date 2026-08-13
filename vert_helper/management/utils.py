from __future__ import annotations

import os

from django.conf import settings
from django.contrib.auth import get_user_model


def create_helper_auth_user(stdout=None, style=None) -> str | None:
    """
    Cria o usuário de autenticação do Helper a partir de variáveis de ambiente.

    Args:
        stdout: Stream de saída (opcional, para Django management commands)
        style: Objeto de estilo para colorização (opcional, para Django management commands)

    Returns:
        Mensagem descritiva da ação realizada ou None se as variáveis não estão configuradas.
    """
    email = os.getenv("HELPER_API_AUTH_EMAIL", "").strip()
    password = os.getenv("HELPER_API_AUTH_PASSWORD", "").strip()

    if not email or not password:
        return None
    # Caso usuário tenha alterado model padrão do User, alterar para model correta:
    User = get_user_model() if not hasattr(settings, "AUTH_USER_MODEL") else settings.AUTH_USER_MODEL
    if isinstance(User, str):
        from django.apps import apps
        User = apps.get_model(User)
    # Verifica se o usuário já existe
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        try:
            existing_user.name = "Helper"
        except:
            existing_user.first_name = "Helper"
            existing_user.last_name = ""
        existing_user.set_password(password)
        existing_user.is_staff = True
        existing_user.is_superuser = True
        existing_user.save()

        message = f"Usuário 'Helper' com email '{email}' atualizado."
        if stdout and style:
            stdout.write(style.WARNING(message))
        return message

    # Cria o novo usuário
    try:
        User.objects.create_user(
            name="Helper",
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
        )
    except:
        User.objects.create_user(
            first_name="Helper",
            last_name="",
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
        )

    message = f"Usuário 'Helper' criado com sucesso com email '{email}'."
    if stdout and style:
        stdout.write(style.SUCCESS(message))
    return message
