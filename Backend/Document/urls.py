from django.urls import path
from . import views
from .views import SilentLoginView, SilentLogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.show_files, name='show_files'),
    path('file/<int:file_id>/', views.view_file, name='view_file'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    path('file/<int:file_id>/report/', views.view_report, name='view_report'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', SilentLoginView.as_view(), name='login'),
    path('logout/', SilentLogoutView.as_view(), name='logout'),
    path('visuals/<int:file_id>/', views.show_visuals, name='show_visuals'),
    path('get_visual_data/<int:file_id>/', views.get_visual_data, name='get_visual_data'),
]