from django.contrib import admin

from .models import Category, Location, Ticket


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "priority",
        "category",
        "location",
        "requester",
        "technician",
        "due_at",
        "created_at",
    )
    list_filter = ("status", "priority", "category", "location")
    search_fields = ("description", "requester__username", "technician__username")
    raw_id_fields = ("requester", "technician")
    readonly_fields = ("created_at", "updated_at")
