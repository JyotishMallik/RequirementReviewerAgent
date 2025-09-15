import os
import PyPDF2
import docx

def extract_text_from_file(file_obj):
    file_path = file_obj.file.path
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

    elif ext in [".docx"]:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif ext in [".txt"]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    else:
        text = "Unsupported file format."

    return text

PROMPT_TEMPLATE = """
You are an AI requirement reviewer. Analyze the following requirement document text and identify issues under these categories:

1. Ambiguity: vague terms like "fast", "user-friendly".
2. Incompleteness: missing details (who, what, when, how).
3. Lack of clarity: inconsistent or contradictory requirements.
4. Missing acceptance criteria: no measurable validation.

Return the analysis in a structured format (Markdown with sections).
"""