
from django import forms
from .models import Issue


class IssueForm(forms.ModelForm):

    class Meta:
        model = Issue

        fields = [
            'title',
            'description',
            'category',
            'latitude',
            'longitude',
            'address',
            'photo',
            'priority',
        ]

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe community issue...'
            }),

            'latitude': forms.NumberInput(attrs={
                'step': 'any',
                'placeholder': 'e.g. 14.5995'
            }),

            'longitude': forms.NumberInput(attrs={
                'step': 'any',
                'placeholder': 'e.g. 120.9842'
            }),

            'address': forms.TextInput(attrs={
                'placeholder': 'Enter address'
            }),
        }
