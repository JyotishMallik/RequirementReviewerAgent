from django.db import models

# Create your models here.
class UploadFile(models.Model):
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=100, default='Jyotish Mallik')
    file_type = models.CharField(max_length=100, default='png')
    file_size = models.PositiveIntegerField(default=100)
    insights = models.TextField(blank=True, null=True)
