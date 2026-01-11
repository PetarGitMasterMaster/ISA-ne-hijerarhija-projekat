from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.core.signing import dumps, loads
from django.conf import settings
from django.contrib.auth import get_user_model
from .forms import RegisterForm

User = get_user_model()


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.is_active = False
            user.save()

            token = dumps(user.pk)
            activation_link = request.build_absolute_uri(
                f"/accounts/activate/{token}/"
            )

            send_mail(
                "Activate your Jutjubić account",
                f"Click to activate your account:\n{activation_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )

            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def activate_account(request, token):
    user_id = loads(token)
    user = User.objects.get(pk=user_id)
    user.is_active = True
    user.save()
    return render(request, "accounts/activated.html")



#from django.shortcuts import render

# Create your views here.
