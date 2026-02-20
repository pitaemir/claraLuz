from django.contrib import admin
from .models import LattesRequest, LattesDocument

class LattesDocumentInline(admin.TabularInline):
    model = LattesDocument
    extra = 0
    fields = ("doc_type", "description", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)

@admin.register(LattesRequest)
class LattesRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "whatsapp", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "whatsapp")
    readonly_fields = ("created_at", "updated_at")
    inlines = [LattesDocumentInline]

@admin.register(LattesDocument)
class LattesDocumentAdmin(admin.ModelAdmin):
    list_display = ("request", "doc_type", "description", "uploaded_at")
    list_filter = ("doc_type", "uploaded_at")
    search_fields = ("request__full_name", "description")
