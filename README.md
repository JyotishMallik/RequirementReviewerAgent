# RequirementReviewerAgent — Setup Guide

Follow these steps to run the project locally.

1. Clone the repository: repository_url = <url>https://github.com/JyotishMallik/RequirementReviewerAgent.git</url>

```
git clone <repository_url>
cd RequirementReviewerAgent
```

2. Add a valid Gemini API Key in `Backend/Agent/settings.py`:

- Open `Backend/Agent/settings.py` and add a line (replace with your key):

```
GEMINI_API_KEY = "your_gemini_api_key_here"
```

3. Open the terminal.

4. Activate the virtual environment (Windows examples):

PowerShell:

```
.venv\Scripts\Activate.ps1
```

Command Prompt:

```
.venv\Scripts\activate.bat
```

(If your venv folder name differs, adjust the path accordingly.)

5. Go inside the `Backend` folder:

```
cd Backend
```

6. Install Python dependencies:

```
pip install -r requirements.txt
```

7. Run the Django development server:

```
python manage.py runserver
```

8. Open the application in your browser:

- Visit `http://127.0.0.1:8000/` (or the URL shown in the terminal).

Notes:

- Replace placeholders (`<repository_url>`, `your_gemini_api_key_here`) with real values.
- If you prefer environment variables, you can load the key from the environment and reference it inside `Backend/Agent/settings.py`.
