from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"style": "color: darkred;"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"style": "color: darkred;"})
    )

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "address"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned

     




