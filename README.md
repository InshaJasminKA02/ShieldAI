# ShieldAI Prompt Injection Detector

ShieldAI is a Flask web app that screens prompts before sending them to an LLM provider. It combines a trained TF-IDF Logistic Regression model with rule-based checks for common jailbreak and malicious instruction patterns.

## Features

- Admin login and protected dashboard
- Prompt injection detection API
- Protected chat UI with provider selection
- Support for Groq, OpenAI, Gemini, Anthropic, Cohere, and Mistral APIs
- SQLite logging for detections
- Stats and CSV export for detection history
- Training and dataset preparation scripts

## Project Structure

- `app.py` - Flask app, routes, detection logic, and logging
- `llm.py` - LLM provider integrations
- `train_model.py` - trains and saves the classifier and vectorizer
- `prepare_data.py` - builds `datasets/final_dataset.csv`
- `test_model.py` - quick local model smoke test
- `templates/` - login, chat, and admin pages
- `datasets/` - source and final training datasets
- `model.pkl` and `vectorizer.pkl` - trained model artifacts

## Setup

Create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set local configuration:

```powershell
$env:SHIELDAI_SECRET_KEY = "replace-with-a-random-secret"
$env:SHIELDAI_ADMIN_USERNAME = "admin"
$env:SHIELDAI_ADMIN_PASSWORD = "choose-a-strong-password"
$env:SHIELDAI_USER_USERNAME = "user"
$env:SHIELDAI_USER_PASSWORD = "choose-a-user-password"
```

Run the app:

```powershell
python app.py
```

Open `http://127.0.0.1:5001/user-login` for the chatbot.
Open `http://127.0.0.1:5001/login` for the admin dashboard.

## Optional Environment Variables

- `SHIELDAI_SECRET_KEY` - Flask session signing secret
- `SHIELDAI_ADMIN_USERNAME` - admin username, defaults to `admin`
- `SHIELDAI_ADMIN_PASSWORD` - admin password, defaults to `admin123`
- `SHIELDAI_USER_USERNAME` - chatbot username, defaults to `user`
- `SHIELDAI_USER_PASSWORD` - chatbot user password, defaults to `mypassword123`
- `SHIELDAI_DATABASE_URI` - SQLAlchemy database URI, defaults to `sqlite:///detections.db`
- `PORT` - app port, defaults to `5001`
- `FLASK_DEBUG` - set to `1` only during local debugging

## Checks

Run the model smoke test:

```powershell
python test_model.py
```

Run basic Flask route checks:

```powershell
python -c "from app import app; c=app.test_client(); print(c.get('/login').status_code)"
```

## Training

Rebuild the final dataset:

```powershell
python prepare_data.py
```

Train a fresh model:

```powershell
python train_model.py
```

This writes `model.pkl` and `vectorizer.pkl`.
