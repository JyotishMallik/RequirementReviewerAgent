from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm

# ----------------------------
# File Upload Model
# ----------------------------
class UploadFile(models.Model):
    req_file_name = models.CharField(max_length=255, blank=True, null=True)
    req_file = models.FileField(upload_to='req_docs/', blank=True, null=True)
    req_file_type = models.CharField(max_length=100, default='application/octet-stream', blank=True, null=True)
    req_file_size = models.PositiveIntegerField(default=0, null=True)
    
    rule_file_name = models.CharField(max_length=255, blank=True, null=True)
    rule_file = models.FileField(upload_to='rule_docs/', blank=True, null=True)
    rule_file_type = models.CharField(max_length=100, default='application/octet-stream', blank=True, null=True)
    rule_file_size = models.PositiveIntegerField(default=0, null=True)
    
    insights = models.TextField(blank=True, null=True)
    check_type = models.CharField(max_length=50, blank=True, null=True)
    visual_data = models.JSONField(blank=True, null=True)

    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        uploader = self.uploaded_by.get_full_name() if self.uploaded_by else 'Unknown'
        return f"{self.req_file_name} (Uploaded by: {uploader})"


# ----------------------------
# Custom User Creation Form
# ----------------------------
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
        label='First Name'
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
        label='Last Name'
    )
    email = forms.EmailField(
        max_length=254, required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
        label='Email'
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')