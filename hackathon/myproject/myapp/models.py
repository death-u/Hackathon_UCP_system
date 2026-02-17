from django.db import models
from django.contrib.auth.models import User


class Policy(models.Model):
    POLICY_TYPES = [
        ('health', 'Health'),
        ('car', 'Car'),
        ('property', 'Property'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="policies")
    policy_number = models.CharField(max_length=50, unique=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    coverage_limit = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.policy_number} - {self.user.username}"


class Claim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="claims")
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="claims")

    title = models.CharField(max_length=200)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_risk_score = models.FloatField(default=0.0)

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.policy.policy_number} - {self.title} - {self.user.username} - {self.user.first_name}"
