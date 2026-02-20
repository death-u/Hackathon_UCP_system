from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from django.urls import reverse

from .models import Claim, Policy
from decimal import Decimal
import random
import os
from .ai_groq import analyze_claim_text
from .vision import analyze_image

def index(request):
    # Just render the homepage with forms
    return render(request, 'pages/index.html')


# def register_view(request):

#     # note username = email.
#     # title = user claim.
#     # status this are the state it's in.
#     # email = user email.
#     # first_name = user full name.

#     if request.method == "POST":
#         full_name = request.POST.get("full_name")
#         email = request.POST.get("email")
#         password = request.POST.get("password")
#         c_password = request.POST.get("c_password")

#         if password != c_password:
#             messages.error(request, "Passwords do not match.")
#             print("Passwords do not match.")
#             return redirect('index')

#         if User.objects.filter(username=email).exists():
#             messages.error(request, "User already exists.")
#             print("User already exists.")
#             return redirect('index')

#         # Create user
#         user = User.objects.create_user(
#             username=email,
#             email=email,
#             password=password,
#             first_name=full_name
#         )
#         # this is a dummy claim for db testing
#         Claim.objects.create(
#             user=user,
#             title="Demo Claim",
#             description="This is a demo claim created automatically.",
#             claim_amount=0.0,
#             status='pending',
#             ai_risk_score=0.0
#         )

#         messages.success(request, "Account created successfully. You can now log in.")
#         print("Account created successfully.")
#         return redirect('index')
#     else:
#         return redirect('index')
def register_view(request):

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        c_password = request.POST.get("c_password")

        if password != c_password:
            messages.error(request, "Passwords do not match.")
            return redirect('index')

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists.")
            return redirect('index')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        # Automatically create demo policy for user
        Policy.objects.create(
            user=user,
            policy_number=f"POL-{random.randint(10000,99999)}",
            policy_type='health',
            coverage_limit=Decimal('500000.00'),
            is_active=True
        )
        # second dummy policy for testing
        Policy.objects.create(
            user=user,
            policy_number=f"POL-{random.randint(10000,99999)}",
            policy_type='any',
            coverage_limit=Decimal('500000.00'),
            is_active=True
        )
        # third dummy policy for testing
        Policy.objects.create(
            user=user,
            policy_number=f"POL-{random.randint(10000,99999)}",
            policy_type='car',
            coverage_limit=Decimal('500000.00'),
            is_active=True
        )
        # fourth dummy policy for testing
        Policy.objects.create(
            user=user,
            policy_number=f"POL-{random.randint(10000,99999)}",
            policy_type='property',
            coverage_limit=Decimal('500000.00'),
            is_active=True
        )

        messages.success(request, "Account created successfully.")
        return redirect('index')

    return redirect('index')



# def login_view(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         user = authenticate(request, username=email, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('dashboard')
#         else:
#             messages.error(request, "Invalid email or password. or account does not exist.")
#             print("Invalid email or password.")
#             return redirect('index')
#     else:
#         return redirect('index')
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password. or account does not exist.")
            return redirect('index')

    return redirect('index')




# def dashboard(request):
#     claims = Claim.objects.filter(user=request.user)
#     contex = {
#         'claims': claims
#         }
#     return render(request, 'pages/dashboard.html',contex)
@login_required(login_url='login')
def dashboard(request):
    claims = Claim.objects.filter(user=request.user)
    policies = Policy.objects.filter(user=request.user, is_active=True)

    context = {
        'claims': claims,
        'policies': policies,
        'coverage_limits': Policy.objects.filter(user=request.user, is_active=True).first().coverage_limit if policies.exists() else 0
    }

    return render(request, 'pages/dashboard.html', context)


@login_required(login_url='login')
def claims_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

    policy_id = request.POST.get("policy_id")
    amount = request.POST.get("amount")
    description = request.POST.get("description")
    file = request.FILES.get("file")

    if not policy_id or not amount or not description:
        return JsonResponse({"status": "error", "message": "Missing fields."}, status=400)

    if not file:
        return JsonResponse({"status": "error", "message": "No file uploaded."}, status=400)

    policy = Policy.objects.filter(id=policy_id, user=request.user, is_active=True).first()
    if not policy:
        return JsonResponse({"status": "error", "message": "Invalid policy selected."}, status=400)

    try:
        claim_amount = Decimal(amount)
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid amount."}, status=400)

    if claim_amount > policy.coverage_limit:
        return JsonResponse({"status": "error", "message": "Claim exceeds policy coverage limit."}, status=400)

    
    claim = Claim.objects.create(
        user=request.user,
        policy=policy,
        title=f"Claim for {policy.policy_number}",
        description=description,
        claim_amount=claim_amount,
        status="pending",
        ai_risk_score=0.0
    )

    
    claim.evidence = file
    claim.save()
    # --- Vision analysis (image -> text) ---
    vision_text = "No vision analysis performed."
    try:
        # This is the absolute path to the saved evidence file
        evidence_path = claim.evidence.path
        vision_text = analyze_image(evidence_path)
    except Exception as e:
        vision_text = f"Vision analysis failed: {str(e)[:120]}"

    
    try:
        combined_description = (
            f"USER DESCRIPTION:\n{description}\n\n"
            f"VISION EVIDENCE SUMMARY:\n{vision_text}"
        )
        ai_result = analyze_claim_text(
        description=combined_description,
        amount=str(claim_amount),
        coverage_limit=str(policy.coverage_limit),
        policy_type=policy.policy_type
        )

        claim.ai_risk_score = ai_result["risk_score"]
        claim.ai_risk_level = ai_result["risk_level"]
        claim.ai_summary = ai_result["summary"]
        claim.ai_recommendation = ai_result["recommendation"]
        claim.ai_flags = ai_result["flags"]
        claim.vision_text = vision_text

        # Optional: set status automatically based on recommendation
        if claim.ai_recommendation == "auto-approve":
            claim.status = "processing"  # or "approved" if you want
        elif claim.ai_recommendation == "flag-suspicious":
            claim.status = "processing"  # or keep pending but flagged

        claim.save()


    except Exception as e:
        claim.ai_risk_score = 5.0
        claim.ai_risk_level = "medium"
        claim.ai_recommendation = "needs-review"
        claim.ai_summary = "AI analysis temporarily unavailable."
        claim.ai_flags = [str(e)[:160]]
        claim.save()

    
    return JsonResponse({
        "status": "success",
        "message": "Claim submitted successfully.",
        "stored_path": claim.evidence.name,
        "redirect_url": reverse("dashboard"),
        "ai": {
            "risk_score": claim.ai_risk_score,
            "risk_level": getattr(claim, "ai_risk_level", None),
            "recommendation": getattr(claim, "ai_recommendation", None),
        }
    })



def logout_view(request):
    logout(request)
    return redirect('index')
