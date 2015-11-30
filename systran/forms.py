from django import forms
from captcha.fields import ReCaptchaField

class OpinionForm(forms.Form):
    sentence = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
