from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.show_files, name='show_files'),
    path('file/<int:file_id>/', views.view_file, name='view_file'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    path('file/<int:file_id>/report/', views.view_report, name='view_report'),
]