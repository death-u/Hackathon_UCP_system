# from django.db import models


# # Create your models here.

from django.db import models
from django.contrib.auth.models import User


class Claim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_risk_score = models.FloatField(default=0.0)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.status} - {self.user.email} - {self.user.first_name} "


# note username = email.
# title = user claim
# status this are the state it's in 
# email = user email
# first_name = user full name