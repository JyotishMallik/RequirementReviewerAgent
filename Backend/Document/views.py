from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse, FileResponse
import os
from .models import UploadFile
from .utils import extract_text_from_file, PROMPT_TEMPLATE
import google.generativeai as genai
from google.genai import types
from google import genai
import markdown2
from ..Agent import settings







# Upload file view
def upload_file(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES.get('document')

            if not uploaded_file:
                return HttpResponse("No file selected", status=400)

            file_name = request.POST.get('fileName') or uploaded_file.name
            file_type = request.POST.get('fileType') or uploaded_file.content_type
            file_size = request.POST.get('fileSize') or uploaded_file.size

            # 1. Save file first in DB (without insights yet)
            file_record = UploadFile.objects.create(
                file_name=file_name,
                file=uploaded_file,
                file_type=file_type,
                file_size=file_size,
                insights=""
            )

            # 2. Get file path from saved model
            file_path = file_record.file.path

            # 3. Read file bytes
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # 4. Call Gemini API
            client = genai.Client(api_key = settings.GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type='application/pdf',
                    ),
                    PROMPT_TEMPLATE
                ]
            )

            insights = response.text if hasattr(response, "text") else "No insights generated."

            # 5. Update record with insights
            file_record.insights = insights
            file_record.save()

            messages.success(request, "File uploaded successfully with insights.")
            return redirect('show_files')

        return render(request, 'Document/upload.html')

    except Exception as e:
        return HttpResponse(f"Error occurred: {e}", status=500)

# Show files with pagination view
def show_files(request):
    all_files = UploadFile.objects.all().order_by('-uploaded_at')
    paginator = Paginator(all_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Document/show_files.html', {'page_obj': page_obj})

# View file view
def view_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = file_obj.file.path

    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_obj.file.name)}"'
        return response
    else:
        messages.error(request, "File does not exist on server.")
        return redirect('show_files')

# Delete file view
@require_POST
def delete_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    # Delete file from storage
    if file_obj.file:
        file_obj.file.delete(save=False)
    # Delete DB record
    file_obj.delete()
    messages.success(request, "File deleted successfully.")
    return redirect('show_files')

# Download file view
def download_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    file_path = file_obj.file.path

    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_obj.file.name)}"'
        return response
    else:
        messages.error(request, "File does not exist on server.")
        return redirect('show_files')
    
# Report of the file view
def view_report(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    clean_insights = markdown2.markdown(file_obj.insights or "")
    
    return render(request, "Document/report.html", {
        "file": file_obj,
        "clean_insights": clean_insights
    })