from django.db import models
from django.contrib.auth.models import User


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_app_reports')
    title = models.CharField(max_length=200)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    summary_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"
