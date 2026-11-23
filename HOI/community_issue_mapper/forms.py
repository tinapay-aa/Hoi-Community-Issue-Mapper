from django import forms
from django.db import transaction
from .models import Community, Issue, IssueImage, Location

class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 150}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'is_active': 'Active (visible in the sidebar and when reporting)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            del self.fields['is_active']
            
 
def style_fields(form):
    """Give every widget its Bootstrap class."""
    for field in form.visible_fields():
        w = field.field.widget
        css = 'form-select' if isinstance(w, forms.Select) else 'form-control'
        w.attrs['class'] = (w.attrs.get('class', '') + ' ' + css).strip()
 
 
class IssueForm(forms.ModelForm):
    """Create / edit an issue together with its Location and an optional photo."""
    latitude = forms.DecimalField(
        max_digits=10, decimal_places=7, min_value=-90, max_value=90,
        widget=forms.HiddenInput,
    )
    longitude = forms.DecimalField(
        max_digits=10, decimal_places=7, min_value=-180, max_value=180,
        widget=forms.HiddenInput,
    )
    address = forms.CharField()
    image = forms.ImageField(required=False, label='Photo evidence')
 
    class Meta:
        model = Issue
        fields = ['title', 'description', 'category', 'community']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            loc = self.instance.location
            self.fields['latitude'].initial = loc.latitude
            self.fields['longitude'].initial = loc.longitude
            self.fields['address'].initial = loc.address
            self.fields['community'].disabled = True   # can't move an issue between communities
        else:
            self.fields['community'].queryset = Community.objects.filter(is_active=True)
        style_fields(self)
 
    def clean_address(self):
        # Nominatim display names can be long; the model column is 255 chars
        return self.cleaned_data['address'].strip()[:255]
 
    @transaction.atomic
    def save(self, user=None, commit=True):
        issue = super().save(commit=False)
        creating = issue.pk is None
 
        loc = Location() if creating else issue.location
        loc.latitude = self.cleaned_data['latitude']
        loc.longitude = self.cleaned_data['longitude']
        loc.address = self.cleaned_data['address']
        loc.save()
 
        if creating:
            issue.location = loc
            issue.reported_by = user
        issue.save()
 
        image = self.cleaned_data.get('image')
        if image:
            IssueImage.objects.create(
                issue=issue, uploaded_by=user, image=image, image_type='Evidence'
            )
        return issue
 
 
class IssueStatusForm(forms.Form):
    """Change status. Managers can set anything + priority; reporters can only mark Resolved."""
    status = forms.ChoiceField()
    priority = forms.ChoiceField(choices=Issue.PRIORITY_CHOICES, required=False)
    remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    proof_image = forms.ImageField(required=False, label='Resolution proof photo')
 
    def __init__(self, *args, issue, manager, **kwargs):
        super().__init__(*args, **kwargs)
        self.issue = issue
        if manager:
            self.fields['status'].choices = Issue.STATUS_CHOICES
            self.fields['status'].initial = issue.status
            self.fields['priority'].initial = issue.priority
        else:
            self.fields['status'].choices = [('Resolved', 'Resolved')]
            del self.fields['priority']
        style_fields(self)
 
    def clean(self):
        data = super().clean()
        if (
            data.get('status') == 'Resolved'
            and not data.get('proof_image')
            and not self.issue.images.filter(image_type='Resolution Proof').exists()
        ):
            self.add_error('proof_image', 'Attach a photo as proof before marking this issue resolved.')
        return data