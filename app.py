from functools import wraps
import csv
import io
import os
import pickle
import secrets

from flask import Flask, Response, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from llm import LLM_PROVIDERS, ask_llm

app = Flask(__name__)
app.secret_key = os.environ.get('SHIELDAI_SECRET_KEY') or secrets.token_hex(32)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SHIELDAI_DATABASE_URI', 'sqlite:///detections.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load model
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# Admin credentials
ADMIN_USERNAME = os.environ.get('SHIELDAI_ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('SHIELDAI_ADMIN_PASSWORD', 'admin123')

# User credentials for the chatbot entrance
USER_USERNAME = os.environ.get('SHIELDAI_USER_USERNAME', 'user')
USER_PASSWORD = os.environ.get('SHIELDAI_USER_PASSWORD', 'mypassword123')

# Database model
class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ── ROUTES ──────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('user_login'))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            if request.accept_mimetypes.accept_json or request.path in {'/logs', '/stats'}:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


def user_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'user':
            if request.accept_mimetypes.accept_json or request.path == '/chat':
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('user_login'))
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not ADMIN_PASSWORD:
            return jsonify({'error': 'Admin password is not configured'}), 500
        data = request.get_json(silent=True) or {}
        if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
            session.clear()
            session['role'] = 'admin'
            return jsonify({'success': True})
        return jsonify({'success': False}), 401
    return render_template('login.html')


@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        if not USER_PASSWORD:
            return jsonify({'error': 'User password is not configured'}), 500
        data = request.get_json(silent=True) or {}
        if data.get('username') == USER_USERNAME and data.get('password') == USER_PASSWORD:
            session.clear()
            session['role'] = 'user'
            return jsonify({'success': True})
        return jsonify({'success': False}), 401
    return render_template('user_login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user_login'))

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')
# Known attack keywords — instant flag regardless of ML model
ATTACK_KEYWORDS = [
    'ignore previous instructions', 'ignore all instructions',
    'forget previous', 'forget all previous',
    'you are now', 'you are a', 'pretend you are',
    'act as', 'roleplay as', 'simulate',
    'jailbreak', 'dan mode', 'developer mode',
    'no restrictions', 'without restrictions',
    'reveal your prompt', 'reveal your system',
    'bypass', 'override instructions',
    'hacking methods', 'hack into', 'hack wifi',
    'crack password', 'steal data', 'exploit vulnerability',
    'xss attack', 'ddos',
    'how to make bomb', 'how to make weapon',
    'malware', 'ransomware', 'phishing',
    'ways to destroy', 'how to destroy',
    'how to kill', 'how to hurt',
    'how to harm', 'how to attack',
    'ways to hack', 'how to hack',
    'destroy the world', 'end the world',
    'how to smuggle', 'smuggle weapons',
    'how to make poison',
    'how to blackmail', 'how to launder',
    'how to commit fraud', 'how to break into',
    'how to steal', 'ways to cheat in exams',
    'illegally', 'unauthorized', 'bypass security',
    'circumvent','without getting caught', 'without being caught',
    'undetected', 'untraceable','how to cheat', 'how to manipulate',
    'how to stalk', 'how to spy on',
    'how to track someone', 'how to follow someone',
    'how to access without permission',
    'how to crack', 'brute force',
    'social engineering', 'phishing attack',
    'man in the middle', 'zero day',
    'remote access', 'unauthorized access',
    'how to get into', 'how to break',
    'how to bypass security', 'how to disable security',
    'how to disable firewall', 'how to disable antivirus',
    'how to get free', 'how to pirate',
    'how to clone', 'how to spoof',
    'how to intercept', 'how to eavesdrop',
    'how to doxx', 'personal information of',
    'how to swat', 'bomb threat',
    'shoot people', 'kill people',
    'hurt people', 'harm people',
    'destroy people', 'attack people',
    'how to radicalize', 'extremist',
    'terrorist', 'terrorism',
    'how to traffic', 'human trafficking',
    'child abuse', 'illegal weapons',
    'illegal drugs', 'drug dealing',
    'ignore previous instructions', 'ignore all instructions',
    'ignore all previous', 'disregard previous',
    'disregard all instructions', 'disregard the above',
    'forget previous', 'forget all previous',
    'forget everything', 'forget your instructions',
    'override instructions', 'override your instructions',
    'bypass', 'bypass restrictions', 'bypass safety',
    'bypass filters', 'bypass guidelines',
    'reveal your prompt', 'reveal your system',
    'reveal system prompt', 'show system prompt',
    'print system prompt', 'display system prompt',
    'what are your instructions', 'what is your prompt',
    'repeat your instructions', 'repeat your prompt',
    'output your instructions', 'output your system prompt',
    'tell me your instructions', 'tell me your prompt',
    'new instructions', 'updated instructions',
    'your new task', 'your actual task',
    'your real instructions', 'your hidden instructions',
    'escape your instructions', 'ignore the above',
    'ignore everything above', 'ignore everything below',
    'end of instructions', 'start of instructions',
    'system prompt is', 'system message is',

    # Jailbreaks
    'you are now', 'pretend you are',
    'act as', 'roleplay as', 'simulate',
    'jailbreak', 'dan mode', 'developer mode',
    'god mode', 'unrestricted mode', 'evil mode',
    'no restrictions', 'without restrictions',
    'no filters', 'without filters',
    'no rules', 'without rules',
    'no limits', 'without limits',
    'no guidelines', 'without guidelines',
    'no safety', 'without safety',
    'unfiltered', 'uncensored', 'unrestricted',
    'do anything now', 'do anything',
    'anything goes', 'no holds barred',
    'free mode', 'prison break mode',
    'sudo mode', 'admin mode', 'root mode',
    'maintenance mode', 'debug mode',
    'training mode', 'test mode',
    'opposite day', 'evil twin',
    'your true self', 'your real self',
    'without any restrictions', 'free from restrictions',
    'you have no restrictions', 'you have no rules',
    'you have no limits', 'you have no filters',
    'you have no guidelines', 'you have no safety',
    'pretend there are no rules', 'pretend you have no limits',
    'imagine you have no restrictions',
    'character with no restrictions',
    'character with no rules',
    'character with no limits',
    'character with no filters',

    # Urgency and pressure tactics
    'this is urgent', 'this is an emergency',
    'immediately', 'right now', 'do it now',
    'no time to explain', 'trust me',
    'i need this now', 'i need this immediately',
    'do this quickly', 'hurry up',
    'before it is too late', 'before its too late',
    'life depends on it', 'lives are at stake',
    'people will die', 'someone will die',
    'critical situation', 'dire situation',
    'no choice', 'you have no choice',
    'you must do this', 'you have to do this',
    'you are required to', 'you are obligated to',
    'failure to comply', 'if you refuse',
    'or else', 'otherwise people will get hurt',

    # Authority and permission tricks
    'i am your creator', 'i am your developer',
    'i am your admin', 'i am your owner',
    'i am anthropic', 'i am openai',
    'i am google', 'i work for anthropic',
    'i work for openai', 'i work for google',
    'i have permission', 'i have authorization',
    'i am authorized', 'i am permitted',
    'special permission', 'special access',
    'admin access', 'root access',
    'backdoor access', 'master password',
    'override code', 'unlock code',
    'secret code', 'access code',
    'password is', 'passcode is',
    'authorization code', 'verification code',
    'as your admin', 'as your creator',
    'as your developer', 'as your owner',
    'as an authorized user', 'as a trusted user',
    'i am a researcher', 'for research purposes',
    'for educational purposes only',
    'this is just a test', 'this is a simulation',
    'hypothetically speaking', 'just hypothetically',
    'in a fictional world', 'in a story',

    # Hacking
    'hacking methods', 'hack into', 'hack wifi',
    'hack website', 'hack server', 'hack database',
    'hack account', 'hack email', 'hack phone',
    'ways to hack', 'how to hack',
    'crack password', 'brute force password',
    'steal data', 'steal credentials',
    'steal password', 'steal information',
    'exploit vulnerability', 'exploit system',
    'sql injection attack', 'perform sql injection', 'execute sql injection',
    'xss attack', 'ddos',
    'man in the middle', 'zero day exploit',
    'remote access trojan', 'unauthorized access',
    'how to access without permission',
    'how to bypass security', 'how to disable security',
    'how to disable firewall', 'how to disable antivirus',
    'social engineering attack', 'phishing attack',
    'spear phishing', 'brute force attack',
    'how to crack', 'how to spoof',
    'how to intercept', 'how to eavesdrop',
    'how to clone a', 'packet sniffing',
    'port scanning', 'network scanning',
    'vulnerability scanning', 'penetration testing without permission',
    'unauthorized penetration', 'illegal penetration',

    # Weapons and violence
    'how to make bomb', 'how to make a bomb',
    'how to build bomb', 'how to build a bomb',
    'how to make weapon', 'how to make weapons',
    'how to make explosives', 'how to make explosive',
    'how to make poison', 'how to make a poison',
    'how to make gun', 'how to build gun',
    'illegal weapons', 'illegal guns',
    'how to smuggle', 'smuggle weapons',
    'bomb threat', 'shoot people',
    'kill people', 'hurt people',
    'harm people', 'attack people',
    'destroy people', 'ways to kill',
    'ways to hurt', 'ways to harm',
    'how to kill', 'how to hurt',
    'how to harm', 'how to attack',
    'ways to destroy', 'how to destroy',
    'mass shooting', 'school shooting',
    'how to shoot', 'how to stab',
    'how to poison someone', 'how to hurt someone',
    'how to kill someone', 'how to murder',

    # Drugs and illegal substances
    'how to make drugs', 'how to produce drugs',
    'how to synthesize drugs', 'drug synthesis',
    'how to make meth', 'how to make cocaine',
    'how to make heroin', 'illegal drugs',
    'drug dealing', 'how to deal drugs',
    'how to traffic drugs', 'drug trafficking',

    # Fraud and crimes
    'how to commit fraud', 'credit card fraud',
    'how to launder money', 'money laundering',
    'how to blackmail', 'how to extort',
    'how to steal', 'how to rob',
    'how to break into', 'how to pick a lock',
    'how to steal a car', 'how to hotwire',
    'identity theft', 'how to steal identity',
    'how to forge', 'how to counterfeit',
    'how to pirate', 'piracy methods',
    'how to scam', 'scamming methods',
    'how to defraud', 'how to deceive',
    'how to manipulate someone', 'manipulation tactics',

    # Surveillance and stalking
    'how to stalk', 'how to spy on',
    'how to track someone', 'how to follow someone',
    'how to monitor someone', 'how to surveil',
    'how to doxx', 'doxing methods',
    'personal information of', 'how to find address of',
    'how to find location of', 'how to find someone',
    'how to locate someone', 'how to track location',

    # Extremism and terrorism
    'how to radicalize', 'radicalization methods',
    'extremist', 'extremism',
    'terrorist', 'terrorism',
    'how to recruit for', 'extremist recruitment',
    'how to swat', 'swatting methods',
    'bomb making', 'bomb assembly',
    'jihad', 'holy war attack',
    'white supremacy', 'neo nazi',

    # Malware and cyber attacks
    'malware', 'ransomware', 'phishing',
    'spyware', 'keylogger', 'rootkit',
    'trojan horse', 'worm virus',
    'how to write malware', 'how to create virus',
    'how to create malware', 'how to deploy ransomware',
    'how to infect', 'how to spread virus',
    'botnet', 'command and control server',
    'cryptojacking', 'drive by download',

    # Human trafficking
    'how to traffic', 'human trafficking',
    'child abuse', 'child exploitation',
    'child pornography', 'underage',

    # Evasion phrases
    'without getting caught', 'without being caught',
    'without leaving trace', 'without leaving traces',
    'undetected', 'untraceable',
    'illegally', 'illegal way', 'illegal methods',
    'against the law', 'break the law',
    'evade police', 'evade detection',
    'evade security', 'avoid detection',
    'avoid getting caught', 'cover my tracks',
    'destroy evidence', 'hide evidence',
    'delete logs', 'clear logs',
    'remain anonymous', 'stay anonymous',
    'hide my identity', 'fake identity',
    'fake my location', 'hide my location',
    'hide my ip', 'mask my ip',

    # Manipulation of AI
    'you are a different ai', 'you are not claude',
    'you are not chatgpt', 'you are not gemini',
    'pretend you are a different ai',
    'your safety training is off',
    'your safety is disabled',
    'your filter is off', 'your filter is disabled',
    'safety mode off', 'safety is off',
    'content filter off', 'content filter disabled',
    'you were trained differently',
    'your real training', 'your actual training',
    'before your safety training',
    'without your safety training',
    'ignore your training', 'ignore your safety training',
    'your training was wrong',
    'your guidelines are wrong',
    'your rules are wrong',
    'your restrictions are wrong',

]
# Whitelist — educational phrases that should never be blocked
SAFE_WHITELIST = [
    'explain', 'what is', 'how does', 'define',
    'for education', 'for learning', 'for awareness',
    'security class', 'awareness class', 'for a class',
    'high level', 'in simple terms', 'basics of',
    'introduction to', 'overview of', 'teach me',
    'help me understand', 'can you explain',
]

def whitelist_check(prompt):
    prompt_lower = prompt.lower()
    for phrase in SAFE_WHITELIST:
        if phrase in prompt_lower:
            return True
    return False

BROAD_CONTEXT_KEYWORDS = {
    'act as',
    'roleplay as',
    'simulate',
    'pretend you are',
    'you are a',
    'you are now',
    'sql injection attack',
    'xss attack',
    'ddos',
    'malware',
    'ransomware',
    'phishing',
    'social engineering',
    'man in the middle',
    'zero day',
}


def rule_based_check(prompt):
    prompt_lower = prompt.lower()
    matched_keywords = []
    for keyword in ATTACK_KEYWORDS:
        if keyword in prompt_lower:
            matched_keywords.append(keyword)

    if not matched_keywords:
        return False

    # Broad or educational terms are sent to the ML model unless another
    # clearly malicious rule also matched.
    return any(keyword not in BROAD_CONTEXT_KEYWORDS for keyword in matched_keywords)


def evaluate_prompt(prompt):
    vec = vectorizer.transform([prompt])
    prediction = model.predict(vec)[0]
    confidence = model.predict_proba(vec)[0]
    confidence_score = round(float(max(confidence)) * 100, 2)
    if whitelist_check(prompt):
        result = 'safe'
    elif rule_based_check(prompt):
        result = 'attack'
    elif prediction == 1 and confidence_score >= 85:
        result = 'attack'
    else:
        result = 'safe'

    return result, confidence_score

@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    result, confidence_score = evaluate_prompt(prompt)

    detection = Detection(
        prompt=prompt,
        result=result,
        confidence=confidence_score
    )
    db.session.add(detection)
    db.session.commit()

    return jsonify({
        'prompt': prompt,
        'result': result,
        'confidence': confidence_score
    })

@app.route('/logs')
@admin_required
def logs():
    detections = Detection.query.order_by(Detection.timestamp.desc()).all()
    return jsonify([{
        'id': d.id,
        'prompt': d.prompt,
        'result': d.result,
        'confidence': d.confidence,
        'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for d in detections])

@app.route('/stats')
@admin_required
def stats():
    total = Detection.query.count()
    attacks = Detection.query.filter_by(result='attack').count()
    safe = Detection.query.filter_by(result='safe').count()
    return jsonify({'total': total, 'attacks': attacks, 'safe': safe})


@app.route('/chat', methods=['POST'])
@user_required
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')
    api_key = data.get('api_key', '')
    provider = data.get('provider', 'groq')

    if not prompt or not api_key:
        return jsonify({'error': 'Missing prompt or API key'}), 400

    if provider not in LLM_PROVIDERS:
        return jsonify({'error': 'Unsupported LLM provider'}), 400

    result, confidence_score = evaluate_prompt(prompt)

    # Save to database
    detection = Detection(
        prompt=prompt,
        result=result,
        confidence=confidence_score
    )
    db.session.add(detection)
    db.session.commit()

    # Block if attack
    if result == 'attack':
        provider_info = LLM_PROVIDERS[provider]
        return jsonify({
            'blocked': True,
            'result': 'attack',
            'confidence': confidence_score,
            'response': None,
            'message': 'This prompt was blocked by ShieldAI - potential injection attack detected.',
            'provider': provider,
            'provider_name': provider_info['name'],
            'model': provider_info['model']
        })

    # Safe; send to selected LLM provider.
    try:
        llm_response = ask_llm(prompt, api_key, provider)
        provider_info = LLM_PROVIDERS[provider]

        print(f"=== {provider_info['name']} RESPONSE ===")
        print(llm_response)
        print(type(llm_response))

        return jsonify({
            'blocked': False,
            'result': 'safe',
            'confidence': confidence_score,
            'response': llm_response,
            'provider': provider,
            'provider_name': provider_info['name'],
            'model': provider_info['model']
        })
    except Exception as e:
        return jsonify({'error': f'{LLM_PROVIDERS[provider]["name"]} error: {str(e)}'}), 500
@app.route('/chat-ui')
@user_required
def chat_ui():
    return render_template('chat.html')


@app.route('/export')
@admin_required
def export():
    detections = Detection.query.order_by(Detection.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(['ID', 'Prompt', 'Result', 'Confidence', 'Timestamp'])

    # Data rows
    for d in detections:
        writer.writerow([d.id, d.prompt, d.result, d.confidence, d.timestamp.strftime('%Y-%m-%d %H:%M:%S')])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=shieldai_logs.csv'}
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
