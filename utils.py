import streamlit as st
import requests
import base64
import io
import re
import uuid
import pandas as pd
from PIL import Image
import config  # imports supabase, HF_TOKEN, API_URL from config module


# ==========================================
# TEXT CLEANING & VALIDATION
# ==========================================

def clean_text(text):
    """Clean text but preserve structure."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    return text.strip()


def validate_score(score, min_val=0, max_val=100):
    """Validate and clamp scores to range."""
    try:
        score = int(score)
        return max(min_val, min(max_val, score))
    except:
        return 50  # Default middle score if parsing fails


# ==========================================
# REPORT PARSING
# ==========================================

def parse_report(text):
    """Enhanced parsing with validation — extracts all tagged sections from AI response."""
    sections = {
        "score": 50,
        "tags": [],
        "tech": "Analysis pending...",
        "psych": "Analysis pending...",
        "risk": "Analysis pending...",
        "fix": "Analysis pending...",
        "overall_grade": "C",
        "entry_quality": 50,
        "exit_quality": 50,
        "risk_score": 50,
        "strength": "Analyzing...",
        "critical_error": "Analyzing..."
    }

    text = clean_text(text)

    # --- Numeric / grade fields ---
    score_match = re.search(r'\[SCORE\]\s*(\d+)', text, re.IGNORECASE)
    if score_match:
        sections['score'] = validate_score(score_match.group(1))

    grade_match = re.search(r'\[OVERALL_GRADE\]\s*([A-FS][\-\+]?(?:-Tier)?)', text, re.IGNORECASE)
    if grade_match:
        sections['overall_grade'] = grade_match.group(1).upper()

    entry_match = re.search(r'\[ENTRY_QUALITY\]\s*(\d+)', text, re.IGNORECASE)
    if entry_match:
        sections['entry_quality'] = validate_score(entry_match.group(1))

    exit_match = re.search(r'\[EXIT_QUALITY\]\s*(\d+)', text, re.IGNORECASE)
    if exit_match:
        sections['exit_quality'] = validate_score(exit_match.group(1))

    risk_score_match = re.search(r'\[RISK_SCORE\]\s*(\d+)', text, re.IGNORECASE)
    if risk_score_match:
        sections['risk_score'] = validate_score(risk_score_match.group(1))

    # --- Tags ---
    tags_match = re.search(r'\[TAGS\](.*?)(?=\[|$)', text, re.DOTALL | re.IGNORECASE)
    if tags_match:
        raw = tags_match.group(1).replace('[', '').replace(']', '').split(',')
        sections['tags'] = [t.strip() for t in raw if t.strip() and len(t.strip()) > 2][:10]

    # --- Text sections ---
    patterns = {
        "tech": r"\[TECH\](.*?)(?=\[PSYCH\]|\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "psych": r"\[PSYCH\](.*?)(?=\[RISK\]|\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "risk": r"\[RISK\](.*?)(?=\[FIX\]|\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "fix": r"\[FIX\](.*?)(?=\[STRENGTH\]|\[CRITICAL_ERROR\]|$)",
        "strength": r"\[STRENGTH\](.*?)(?=\[CRITICAL_ERROR\]|$)",
        "critical_error": r"\[CRITICAL_ERROR\](.*?)$"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'```[\s\S]*?```', '', content)
            if len(content) > 10:
                sections[key] = content

    return sections


# ==========================================
# DATABASE
# ==========================================

def save_analysis(user_id, data, ticker_symbol="UNK", img_url=None):
    """Persist a completed analysis to Supabase."""
    if not config.supabase:
        return
    try:
        payload = {
            "user_id": user_id,
            "ticker": ticker_symbol,
            "score": data.get('score', 50),
            "mistake_tags": data.get('tags', []),
            "technical_analysis": data.get('tech', ''),
            "psych_analysis": data.get('psych', ''),
            "risk_analysis": data.get('risk', ''),
            "fix_action": data.get('fix', ''),
            "image_url": img_url
        }
        config.supabase.table("trades").insert(payload).execute()
    except Exception as e:
        st.error(f"Database error: {e}")


# ==========================================
# IMAGE UPLOAD
# ==========================================

def upload_image_to_supabase(file_obj):
    """Upload an image stream to Supabase Storage, return its public URL."""
    if not config.supabase:
        return None
    try:
        file_ext = file_obj.name.split('.')[-1]
        file_name = f"{st.session_state['user']}/{uuid.uuid4()}.{file_ext}"

        file_obj.seek(0)
        file_bytes = file_obj.read()

        bucket_name = "trade_images"
        config.supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=file_name,
            file_options={"content-type": f"image/{file_ext}"}
        )

        public_url = config.supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        st.error(f"Image Upload Failed: {e}")
        return None


def prepare_image_b64(file_obj):
    """Open, resize, and base64-encode an uploaded image for the vision API."""
    image = Image.open(file_obj)
    max_size = (1920, 1080)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# ==========================================
# VISION API CALL
# ==========================================

def call_vision_api(prompt, img_b64, max_retries=2):
    """Call HuggingFace vision model with retry logic and validation."""
    for attempt in range(max_retries):
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ]

            payload = {
                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.3,
                "top_p": 0.95
            }

            headers = {
                "Authorization": f"Bearer {config.HF_TOKEN}",
                "Content-Type": "application/json"
            }

            res = requests.post(config.API_URL, headers=headers, json=payload, timeout=60)

            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                # Guard against model returning HTML/code instead of analysis
                if '<div' in content or '<html' in content or '```' in content[:100]:
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise ValueError("Model returning code instead of analysis")
                return content
            else:
                raise Exception(f"API returned {res.status_code}: {res.text[:200]}")

        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            continue

    raise Exception("Max retries exceeded")


def call_text_api(prompt, max_tokens=1500):
    """Call HuggingFace model with text-only input (no image)."""
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    payload = {
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    headers = {
        "Authorization": f"Bearer {config.HF_TOKEN}",
        "Content-Type": "application/json"
    }
    res = requests.post(config.API_URL, headers=headers, json=payload, timeout=60)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API Error: {res.status_code} — {res.text[:200]}")


# ==========================================
# INSIGHT GENERATION
# ==========================================

def generate_insights(df):
    """Generate AI-style insights from the user's trade history DataFrame."""
    insights = []
    if df.empty:
        return ["Awaiting data to generate neural patterns."]

    recent_scores = df.head(3)['score'].mean()
    if recent_scores < 50:
        insights.append("⚠️ **Tilt Detected:** Last 3 trades avg < 50. Suggest 24h trading halt.")
    elif recent_scores > 80:
        insights.append("🔥 **Flow State:** High decision quality detected. Increase risk tolerance slightly.")

    all_tags = [tag for sublist in df['mistake_tags'] for tag in sublist]
    if "FOMO" in all_tags and "Revenge" in all_tags:
        insights.append("🧠 **Toxic Loop:** 'FOMO' leading to 'Revenge' detected 3x this month.")

    return insights if insights else ["✅ Performance metrics within normal parameters."]
