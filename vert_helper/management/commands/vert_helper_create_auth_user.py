from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError

from vert_helper.management.utils import create_helper_auth_user


class Command(BaseCommand):
    help = "Cria o usuário de autenticação do Helper API a partir de variáveis de ambiente"

    def handle(self, *args, **options):
        email = os.getenv("HELPER_API_AUTH_EMAIL", "").strip()
        password = os.getenv("HELPER_API_AUTH_PASSWORD", "").strip()

        if not email or not password:
            raise CommandError(
                "As variáveis de ambiente HELPER_API_AUTH_EMAIL e "
                "HELPER_API_AUTH_PASSWORD não estão configuradas."
            )

        result = create_helper_auth_user(self.stdout, self.style)
        if not result:
            raise CommandError(
                "Falha ao criar usuário Helper. "
                "Verifique as variáveis de ambiente."
            )
