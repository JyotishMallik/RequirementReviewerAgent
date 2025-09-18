from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import FileResponse, HttpResponse
from django.conf import settings
from .models import UploadFile, CustomUserCreationForm
from django.contrib.auth.models import User
import os
import markdown2
from google import genai
from google.genai import types
from django.utils.dateparse import parse_date
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .utils import PROMPT_TEMPLATE


# ----------------------------
# Auth Views
# ----------------------------
class SilentLoginView(LoginView):
    template_name = 'Document/login.html'

    def form_valid(self, form):
        return super().form_valid(form)  # skip success message


class SilentLogoutView(LogoutView):
    next_page = 'home'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto login
            messages.success(request, "Signup successful! You are now logged in.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'Document/signup.html', {'form': form})


# ----------------------------
# Homepage
# ----------------------------
def home(request):
    return render(request, 'Document/home.html')


# ----------------------------
# Upload File View
# ----------------------------
@login_required
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        if not uploaded_file:
            return HttpResponse("No file selected", status=400)

        # Get metadata from JS
        file_name = request.POST.get('fileName') or uploaded_file.name
        file_type = request.POST.get('fileType') or uploaded_file.content_type
        file_size = request.POST.get('fileSize') or uploaded_file.size

        # Save file record
        file_record = UploadFile.objects.create(
            file_name=file_name,
            file=uploaded_file,
            file_type=file_type,
            file_size=file_size,
            insights="",
            uploaded_by=request.user
        )

        response = None
        try:
            # Read file bytes
            file_path = file_record.file.path
            with open(file_path, "rb") as f:
                file_bytes = f.read()
                
            # Call Gemini API
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=file_type,
                    ),
                    PROMPT_TEMPLATE
                ]
            )
        except:
            print("Model is failing")

        insights = getattr(response, "text", "No insights generated.")

        # Save insights
        file_record.insights = insights
        file_record.save()

        messages.success(request, "File uploaded successfully with insights.")
        return redirect('show_files')

    return render(request, 'Document/upload.html')


# ----------------------------
# Show Files with Filters & Pagination
# ----------------------------
@login_required
def show_files(request):
    all_files = UploadFile.objects.all().order_by('-uploaded_at')

    # Filters
    file_type_filter = request.GET.get('file_type')
    uploaded_by_id = request.GET.get('uploaded_by')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if file_type_filter:
        all_files = all_files.filter(file_type=file_type_filter)
    if uploaded_by_id:
        all_files = all_files.filter(uploaded_by__id=uploaded_by_id)
    if start_date:
        all_files = all_files.filter(uploaded_at__date__gte=parse_date(start_date))
    if end_date:
        all_files = all_files.filter(uploaded_at__date__lte=parse_date(end_date))

    # Distinct values for dropdowns
    file_types = UploadFile.objects.values_list('file_type', flat=True).distinct()
    uploaded_bys = User.objects.all()

    # Pagination
    paginator = Paginator(all_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Document/show_files.html', {
        'page_obj': page_obj,
        'file_types': file_types,
        'uploaded_bys': uploaded_bys,
        'selected_file_type': file_type_filter,
        'selected_uploaded_by': int(uploaded_by_id) if uploaded_by_id else None,
        'start_date': start_date,
        'end_date': end_date,
    })


# ----------------------------
# View File
# ----------------------------
@login_required
def view_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = file_obj.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_obj.file.name)}"'
        return response
    messages.error(request, "File does not exist on server.")
    return redirect('show_files')


# ----------------------------
# Download File
# ----------------------------
@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = file_obj.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_obj.file.name)}"'
        return response
    messages.error(request, "File does not exist on server.")
    return redirect('show_files')


# ----------------------------
# Delete File
# ----------------------------
@login_required
@require_POST
def delete_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    if file_obj.file:
        file_obj.file.delete(save=False)
    file_obj.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('show_files')


# ----------------------------
# View Report (Insights)
# ----------------------------
@login_required
def view_report(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    clean_insights = markdown2.markdown(file_obj.insights or "")
    return render(request, "Document/report.html", {
        "file": file_obj,
        "clean_insights": clean_insights
    })