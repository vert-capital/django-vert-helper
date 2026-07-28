from __future__ import annotations

import os

from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from vert_helper.management.utils import create_helper_auth_user


@receiver(post_migrate)
def create_helper_user(sender, **kwargs):
    """Cria o usuário Helper a partir de variáveis de ambiente."""
    if sender.name != "vert_helper":
        return

    create_helper_auth_user()
