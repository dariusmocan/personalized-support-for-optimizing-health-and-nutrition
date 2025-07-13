from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import QuizResponse

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput)
    password = forms.CharField(widget=forms.PasswordInput)

class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control'}));

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    
    

class QuizForm(forms.ModelForm):
    class Meta:
        model = QuizResponse
        fields = ['age', 'height', 'weight', 'gender', 'objective', 'activity_level']
        widgets = {
            'gender': forms.Select(choices=[('masculin', 'Masculin'), ('feminin', 'Feminin')]),
            'objective': forms.Select(choices=[
                (1, 'Slăbit'),
                (2, 'Punere în greutate'),
                (3, 'Creștere masă musculară'),
                (4, 'Recompoziție corporală')
            ]),
            'activity_level': forms.Select(choices=QuizResponse.ACTIVITY_LEVEL_CHOICES)
        }