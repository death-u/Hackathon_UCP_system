from django.db import models
from django.contrib.auth.models import User


class Policy(models.Model):
    POLICY_TYPES = [
        ('health', 'Health'),
        ('car', 'Car'),
        ('property', 'Property'),
        ('any', 'Any'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="policies")
    policy_number = models.CharField(max_length=50, unique=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    coverage_limit = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        # keep it readable
        return f"{self.policy_number} ({self.get_policy_type_display()}) - {self.user.username}"


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

    # Save evidence file path in DB
    evidence = models.ImageField(upload_to="uploads/", blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_risk_score = models.FloatField(default=0.0)
    date_created = models.DateTimeField(auto_now_add=True)
    ai_summary = models.TextField(blank=True, null=True)
    ai_recommendation = models.CharField(max_length=50, blank=True, null=True)
    ai_flags = models.JSONField(blank=True, null=True)
    ai_risk_level = models.CharField(max_length=10, blank=True, null=True)
    vision_text = models.TextField(blank=True, null=True)


    def __str__(self):
        ev = self.evidence.name if self.evidence else "NoFile"
        return f"{self.policy.policy_number} | {self.title} | {self.user.username} | {self.status} | {ev} | {self.description}"
