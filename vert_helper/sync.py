from __future__ import annotations

from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.db import transaction

from .models import Action, Service, Question
from .registry import get_registered_actions


def autodiscover_actions() -> None:
    for app_config in apps.get_app_configs():
        module_name = f"{app_config.name}.actions"
        try:
            import_module(module_name)
        except ModuleNotFoundError:
            continue


def _get_service_names_from_settings() -> set[str]:
    config = getattr(settings, "VERT_HELPER", {}) or {}
    services_cfg = config.get("SERVICES", {})
    if not isinstance(services_cfg, dict):
        return set()
    return {
        str(name).strip()
        for name in services_cfg.keys()
        if str(name).strip()
    }


@transaction.atomic
def sync_services_from_settings() -> dict[str, int]:
    configured_names = _get_service_names_from_settings()

    created = 0
    reactivated = 0
    deactivated = 0

    existing_services = {s.name: s for s in Service.all_objects.all()}

    for service_name in configured_names:
        service = existing_services.get(service_name)
        if not service:
            Service.all_objects.create(name=service_name, is_active=True)
            created += 1
            continue

        if not service.is_active:
            service.is_active = True
            service.save(update_fields=["is_active", "updated_at"])
            reactivated += 1

    for service in Service.all_objects.filter(is_active=True):
        if service.name not in configured_names:
            service.is_active = False
            service.save(update_fields=["is_active", "updated_at"])
            deactivated += 1

    return {
        "created": created,
        "reactivated": reactivated,
        "deactivated": deactivated,
    }


@transaction.atomic
def _register_action_questions(action: Action, questions: list[dict]) -> None:
    """
     Registra as perguntas associadas a uma ação no banco de dados.
     questions example:
     [
         {
             "label": "Pergunta 1",
             "type": "text",
             "options": ["Opção 1", "Opção 2"],
             "is_required": True,
             "action_kwarg": "pergunta_1",
             "children": [
                 {
                     "label": "Pergunta 1.1",
                     "type": "text",
                     "options": ["Opção 1", "Opção 2"],
                     "is_required": True,
                     "action_kwarg": "pergunta_1_1",
                     "parent_value": "Opção 1",
                 },
                 {
                        "label": "Pergunta 1.2",
                        "type": "text",
                        "options": ["Opção 1", "Opção 2"],
                        "is_required": True,
                        "action_kwarg": "pergunta_1_2",
                        "parent_value": "Opção 2",
                 }
             ]
         }
     ]
    """
    action.questions.all().delete()
    for question_data in questions:
        _create_question_recursive(action, question_data)


def _create_question_recursive(action: Action, question_data: dict, parent: Question | None = None) -> None:
    question = action.questions.create(
        label=question_data["label"],
        type=question_data["type"],
        options=question_data.get("options", []),
        is_required=question_data.get("is_required", False),
        action_kwarg=question_data.get("action_kwarg"),
        parent_question=parent,
        parent_value=question_data.get("parent_value"),
        is_first=True if parent is None else False,
    )
    for child_data in question_data.get("children", []):
        _create_question_recursive(action, child_data, parent=question)


@transaction.atomic
def sync_actions_from_registry() -> dict[str, int]:
    autodiscover_actions()
    registered = get_registered_actions()

    created = 0
    updated = 0
    deleted = 0

    active_services = {s.name: s for s in Service.objects.all()}

    seen_slugs: set[str] = set()
    for slug, action_def in registered.items():
        action, was_created = Action.objects.update_or_create(
            slug=slug,
            defaults={
                "name": action_def.name,
                "description": action_def.description,
                "function_path": action_def.function_path,
                "status": Action.Status.ACTIVE,
            },
        )

        seen_slugs.add(slug)

        service_objects = [
            active_services[name]
            for name in action_def.services
            if name in active_services
        ]
        action.services.set(service_objects)
        if action_def.questions:
            _register_action_questions(action, action_def.questions)

        if was_created:
            created += 1
        else:
            updated += 1

    if seen_slugs:
        deleted, _ = Action.objects.exclude(slug__in=seen_slugs).delete()

    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
    }
