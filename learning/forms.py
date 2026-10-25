# Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Course, Lesson, Question

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=70,label='Your name')
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['first_name','username','email','password1','password2']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title','slug','summary','description','category','level','accent','price','currency','pass_percentage','published']
        widgets = {'description':forms.Textarea(attrs={'rows':5})}

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title','position','minutes','content','video_url']
        widgets = {'content':forms.Textarea(attrs={'rows':14})}

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['position','prompt','option_a','option_b','option_c','option_d','correct']


class ReceiptForm(forms.Form):
    reference = forms.CharField(max_length=120, label='Transfer reference / transaction ID')
    receipt = forms.ImageField(help_text='PNG or JPEG, up to 2 MB. Your receipt is private.')
    def clean_receipt(self):
        receipt = self.cleaned_data['receipt']
        if receipt.size > 2 * 1024 * 1024 or receipt.image.format not in ('PNG','JPEG'):
            raise forms.ValidationError('Upload a PNG or JPEG up to 2 MB.')
        if receipt.image.width * receipt.image.height > 20000000:
            raise forms.ValidationError('Image dimensions are too large.')
        return receipt
