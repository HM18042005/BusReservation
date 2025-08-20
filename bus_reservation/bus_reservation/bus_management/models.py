from django.db import models
from django.contrib.auth import get_user_model
from core.models import Bus, Booking, Review
import uuid

# Create your models here.

class AdminLog(models.Model):
    admin = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.admin.email} - {self.action}"

class Report(models.Model):
    REPORT_TYPE_CHOICES = (
        ('BOOKING', 'Booking Report'),
        ('BUS', 'Bus Report'),
        ('USER', 'User Report'),
        ('REVENUE', 'Revenue Report'),
    )
    
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    generated_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()
    
    def __str__(self):
        return f"{self.report_type} - {self.generated_at}"

class AdminSettings(models.Model):
    setting_key = models.CharField(max_length=50, unique=True)
    setting_value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.setting_key
