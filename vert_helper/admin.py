from django.contrib import admin

from .models import Action, ActionExecution, Question, Service, ServiceHealth


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)

    def get_queryset(self, request):
        return Service.all_objects.all()


@admin.register(ServiceHealth)
class ServiceHealthAdmin(admin.ModelAdmin):
    list_display = ("service", "status", "checked_at")
    list_filter = ("status", "service")
    search_fields = ("service__name", "message")
    readonly_fields = (
        "service",
        "status",
        "message",
        "checked_at",
        "created_at",
    )


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "status", "function_path", "created_at")
    list_filter = ("status", "services")
    search_fields = ("slug", "name", "description", "function_path")
    filter_horizontal = ("services",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("label", "action", "type", "is_required", "is_first")
    list_filter = ("type", "is_required", "is_first", "action")
    search_fields = ("label", "action__slug", "action_kwarg")


@admin.register(ActionExecution)
class ActionExecutionAdmin(admin.ModelAdmin):
    list_display = ("action", "executed_by", "executed_at")
    list_filter = ("action", "executed_at")
    search_fields = ("action__slug",)
    readonly_fields = (
        "action",
        "responses",
        "result",
        "executed_by",
        "executed_at",
        "created_at",
    )
