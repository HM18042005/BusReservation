from django.contrib import admin
from .models import AdminLog, Report, AdminSettings

@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin__email', 'action', 'details')
    readonly_fields = ('timestamp',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_by', 'generated_at')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('report_type', 'generated_by__email')
    readonly_fields = ('report_id', 'generated_at')

@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_key', 'setting_value', 'updated_at')
    search_fields = ('setting_key', 'setting_value')
    readonly_fields = ('updated_at',)
