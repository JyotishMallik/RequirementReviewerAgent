import json
import docx2txt
import pdfplumber
import os
from django.conf import settings
from google.generativeai import GenerativeModel
from google.genai import types
from google.generativeai.types import GenerationConfig
from google import genai

PROMPT_TEMPLATE_START = """
You are an expert Requirements Document Analyst. Your task is to perform a detailed quality and content review of a provided requirements document.

Your analysis must focus on the following core criteria:

"""

PROMPT_TEMPLATE_BASIC = """
1. Clarity & Specificity
Ambiguity: Identify vague or subjective terms and phrases (e.g., "fast," "easy to use," "flexible").

Clarity: Point out any inconsistent, confusing, or contradictory statements.

2. Completeness
Missing Information: Note any missing critical details, such as user roles, a description of the 'what' and 'why', system dependencies, or non-functional requirements (performance, security, scalability).

3. Testability & Measurability
Acceptance Criteria: Determine if each requirement has clear, measurable, and verifiable acceptance criteria. If not, suggest how to make them testable.

4. Quality & Consistency
Correctness: Identify any grammatical errors, typos, or factual mistakes.

Consistency: Check for logical consistency and a uniform tone and style throughout the document.

Conciseness: Flag any redundant information or unnecessary jargon.

5. Feasibility
Technical Feasibility: Evaluate whether the requirements seem realistic and achievable with current technology and resources.

Business Feasibility: Assess if the requirements align with stated business goals and are practical to implement.

"""

PROMPT_TEMPLATE_BASIC_AND_RULE = """"
6. Custom Rules

"""

PROMPT_TEMPLATE_RULE = """"
Custom Rules

"""

PROMPT_TEMPLATE_END = """
Output Format:

Present your findings in a structured, actionable report using Markdown with the following sections:

Summary of Findings: A brief, high-level overview of the document's overall quality.

Detailed Analysis by Category:

Use the H2 headings from the list above (e.g., ## 1. Clarity & Specificity).

Under each heading, provide a summary of your findings for that category.

Use bullet points to list specific examples of issues, quoting the problematic text from the document and providing a clear, actionable suggestion for improvement.

"""

VISUAL_PROMPT = f"""
Analyze the document and provide structured data for visualization in a single JSON object.

The data should include the following keys:
- 'readability_score': A float representing the document's readability (e.g., Flesch-Kincaid scale).
- 'overall_quality_score': An integer (0-100) representing the document's overall quality based on clarity, completeness, and testability.
- 'issue_breakdown': A dictionary where keys are issue categories (e.g., 'Vague Language', 'Incomplete', 'Untestable') and values are the count of each type of issue.
- 'sentiment_distribution': A dictionary with sentiment labels ('positive', 'neutral', 'negative') and their word counts.
- 'key_phrases': An array of strings with the most important and frequently occurring phrases.
- 'compliance_summary': A dictionary with compliance check names as keys and a 'status' ('compliant' or 'non-compliant') and a brief 'note' as values.

ONLY return the JSON object, and nothing else.
"""

def get_gemini_reponse(file_record, file_type, PROMPT_INSIGHTS, PROMPT_VISUAL):

    file_path = file_record.req_file.path
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # 1. First call to get the detailed text insights
        insights_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file_type,
                ),
                PROMPT_INSIGHTS
            ]
        )
    except Exception as e:
        print(f"Failed to Generate the Insights.")
        insights_response = None

    try:
        visual_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file_type,
                ),
                PROMPT_VISUAL
            ],
            config={
                "response_mime_type": "application/json",
            },
        )
        visual_data = json.loads(visual_response.text)
    except Exception as e:
        print(f"Failed to Generate the Visuals.")
        visual_data = {}      

    return insights_response, visual_data
    
def extract_text_from_file(uploaded_file):
    """
    Extracts text from a given PDF or DOCX file.
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    text = ""
    try:
        if file_extension == '.pdf':
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif file_extension == '.docx':
            text = docx2txt.process(uploaded_file)
        else:
            return None # Or raise an error for unsupported file types
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None
    return text