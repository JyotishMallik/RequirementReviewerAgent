import json
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import FileResponse, HttpResponse, JsonResponse
from .models import UploadFile, CustomUserCreationForm
from django.contrib.auth.models import User
import os
import markdown2
from google import genai
from django.utils.dateparse import parse_date
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .utils import extract_text_from_file, get_gemini_reponse, PROMPT_TEMPLATE_START, PROMPT_TEMPLATE_BASIC, PROMPT_TEMPLATE_BASIC_AND_RULE, PROMPT_TEMPLATE_RULE, PROMPT_TEMPLATE_END, VISUAL_PROMPT

# -------------------------------------------------------------------------------------------
# Auth Views
# -------------------------------------------------------------------------------------------

class SilentLoginView(LoginView):
    template_name = 'Document/login.html'

    def form_valid(self, form):
        return super().form_valid(form)


class SilentLogoutView(LogoutView):
    next_page = 'home'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful! You are now logged in.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'Document/signup.html', {'form': form})

# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------------------------

def home(request):
    return render(request, 'Document/home.html')

# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# Upload File View
# ---------------------------------------------------------------------------------------------

@login_required
def upload_file(request):
    if request.method == 'POST':

        PROMPT_INSIGHTS, PROMPT_VISUAL, response = "", "", None
        check_type = request.POST.get('check_type')
        requirement_doc = request.FILES.get('requirement_document')
        req_file_name = requirement_doc.name
        req_file_type = requirement_doc.content_type
        req_file_size = requirement_doc.size
        
        rule_based_doc = None
        rule_file_name = None
        rule_file_type = None
        rule_file_size = None

        if not requirement_doc:
            return HttpResponse("No file selected", status=400)


        if check_type != 'basic_check':
            
            rule_based_doc = request.FILES.get('rule_based_document')
            
            if not rule_based_doc:
                    return HttpResponse('Rule based document is required for this check type.', status=400)
            
            rule_doc_content = extract_text_from_file(rule_based_doc)
           
            if rule_doc_content is None:
                    return HttpResponse('Please upload a valid rule based document.', status=400)
            
            rule_file_name = rule_based_doc.name
            rule_file_type = rule_based_doc.content_type
            rule_file_size = rule_based_doc.size

            if check_type == 'basic_rule_check':
                PROMPT_INSIGHTS = f"{PROMPT_TEMPLATE_START}\n{PROMPT_TEMPLATE_BASIC}\n{PROMPT_TEMPLATE_BASIC_AND_RULE}\n{rule_doc_content}\n\n{PROMPT_TEMPLATE_END}"
            
            else:
                PROMPT_INSIGHTS = f"{PROMPT_TEMPLATE_START}\n{PROMPT_TEMPLATE_RULE}\n{rule_doc_content}\n\n{PROMPT_TEMPLATE_END}"
        
        elif check_type == 'basic_check':
            PROMPT_INSIGHTS = f"{PROMPT_TEMPLATE_START}\n{PROMPT_TEMPLATE_BASIC}\n\n{PROMPT_TEMPLATE_END}"
        
        else:
            return HttpResponse('Invalid check type selected.', status=400)

        # Save file record
        file_record = UploadFile.objects.create(
            req_file_name=req_file_name,
            req_file=requirement_doc,
            req_file_type=req_file_type,
            req_file_size=req_file_size,
            rule_file_name=rule_file_name,
            rule_file=rule_based_doc,
            rule_file_type=rule_file_type,
            rule_file_size=rule_file_size,
            visual_data="{}",
            insights="",
            check_type=check_type,
            uploaded_by=request.user
        )

        insight_response, visual_response = get_gemini_reponse(file_record, req_file_type, PROMPT_INSIGHTS, VISUAL_PROMPT)

        insights = getattr(insight_response, "text", "No insights generated.")

        # Save insights
        file_record.insights = insights
        file_record.visual_data = visual_response
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
        all_files = all_files.filter(req_file_type=file_type_filter)
    if uploaded_by_id:
        all_files = all_files.filter(uploaded_by__id=uploaded_by_id)
    if start_date:
        all_files = all_files.filter(uploaded_at__date__gte=parse_date(start_date))
    if end_date:
        all_files = all_files.filter(uploaded_at__date__lte=parse_date(end_date))

    # Distinct values for dropdowns
    file_types = UploadFile.objects.values_list('req_file_type', flat=True).distinct()
    uploaded_bys = User.objects.all()

    # Pagination
    paginator = Paginator(all_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Document/show_files.html', {
        'requirement_docs': page_obj,
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
    
    # You need to determine which file to serve
    if file_obj.req_file:
        file_path = file_obj.req_file.path
        file_name = file_obj.req_file_name
    elif file_obj.rule_file:
        file_path = file_obj.rule_file.path
        file_name = file_obj.rule_file_name
    else:
        messages.error(request, "File does not exist on server.")
        return redirect('show_files')

    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'inline; filename="{file_name}"'
        return response
    
    messages.error(request, "File does not exist on server.")
    return redirect('show_files')


# ----------------------------
# Download File
# ----------------------------
@login_required
def download_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id)
    
    # You need to determine which file to serve for download
    if file_obj.req_file:
        file_path = file_obj.req_file.path
        file_name = file_obj.req_file_name
    elif file_obj.rule_file:
        file_path = file_obj.rule_file.path
        file_name = file_obj.rule_file_name
    else:
        messages.error(request, "File does not exist on server.")
        return redirect('show_files')

    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response

    messages.error(request, "File does not exist on server.")
    return redirect('show_files')


# ----------------------------
# Delete File
# ----------------------------
@login_required
@require_POST
def delete_file(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id, uploaded_by=request.user)

    if file_obj.req_file:
        file_obj.req_file.delete(save=False)
    
    if file_obj.rule_file:
        file_obj.rule_file.delete(save=False)
        
    file_obj.delete()
    messages.success(request, "File and associated data deleted successfully.")
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


# ----------------------------
# Get Visual Data (New View)
# ----------------------------
@login_required
def get_visual_data(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id, uploaded_by=request.user)
    
    # The visual_data field is already a dictionary because it's a JSONField.
    data = file_obj.visual_data
    
    # Check if the data is not None or empty before returning.
    if data:
        return JsonResponse(data)
    else:
        # Handle cases where the data might be empty or None.
        return JsonResponse({"error": "No visual data found for this file."}, status=404)

# ----------------------------
# View Visuals (Modified View)
# ----------------------------
@login_required
def show_visuals(request, file_id):
    file_obj = get_object_or_404(UploadFile, id=file_id, uploaded_by=request.user)
    return render(request, 'Document/visuals.html', {'file_id': file_id})