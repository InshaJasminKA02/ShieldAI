import requests
from groq import Groq


LLM_PROVIDERS = {
    "groq": {
        "name": "Groq",
        "model": "llama-3.1-8b-instant",
    },
    "openai": {
        "name": "OpenAI",
        "model": "gpt-4o-mini",
    },
    "gemini": {
        "name": "Google Gemini",
        "model": "gemini-1.5-flash",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "model": "claude-3-5-haiku-20241022",
    },
    "cohere": {
        "name": "Cohere",
        "model": "command-r-plus-08-2024",
    },
    "mistral": {
        "name": "Mistral AI",
        "model": "mistral-small-latest",
    },
}


def ask_llm(prompt, api_key, provider="groq"):
    provider = (provider or "groq").lower()
    if provider not in LLM_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    if provider == "groq":
        return ask_groq(prompt, api_key)
    if provider == "openai":
        return ask_openai(prompt, api_key)
    if provider == "gemini":
        return ask_gemini(prompt, api_key)
    if provider == "anthropic":
        return ask_anthropic(prompt, api_key)
    if provider == "cohere":
        return ask_cohere(prompt, api_key)
    if provider == "mistral":
        return ask_mistral(prompt, api_key)

    raise ValueError(f"Unsupported LLM provider: {provider}")


def ask_groq(prompt, api_key):
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=LLM_PROVIDERS["groq"]["model"],
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def ask_openai(prompt, api_key):
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_PROVIDERS["openai"]["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 900,
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def ask_gemini(prompt, api_key):
    model = LLM_PROVIDERS["gemini"]["model"]
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 900,
            },
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    parts = data["candidates"][0]["content"].get("parts", [])
    return "".join(part.get("text", "") for part in parts).strip()


def ask_anthropic(prompt, api_key):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_PROVIDERS["anthropic"]["model"],
            "max_tokens": 900,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return "".join(part.get("text", "") for part in data.get("content", [])).strip()


def ask_cohere(prompt, api_key):
    response = requests.post(
        "https://api.cohere.com/v2/chat",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_PROVIDERS["cohere"]["model"],
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    content = data.get("message", {}).get("content", [])
    return "".join(part.get("text", "") for part in content).strip()


def ask_mistral(prompt, api_key):
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_PROVIDERS["mistral"]["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 900,
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
