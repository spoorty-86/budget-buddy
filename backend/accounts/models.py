from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Extra info per user (Milestone 1 - Users/Profiles schema)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    monthly_income_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"
