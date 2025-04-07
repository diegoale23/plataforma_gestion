# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Skill

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Habilidades"
    )
    bio = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Biografía"
    )
    location = forms.CharField(max_length=100, required=False, label="Ubicación")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.skills.set(self.cleaned_data['skills'])
            profile.bio = self.cleaned_data['bio']
            profile.location = self.cleaned_data['location']
            profile.save()
        return user