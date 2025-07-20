import os
import uuid
import re
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from gtts import gTTS
from groq import Groq
from difflib import SequenceMatcher
import requests
from google.cloud import vision
from google.cloud.vision_v1 import types
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
app.secret_key = 'linguaai_secret_key'

AUDIO_DIR = os.path.join('static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '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')
groq_client = Groq(api_key=GROQ_API_KEY)

GTTS_LANG_CODES = {
    'english': 'en',
    'hindi': 'hi',
}

LANGUAGE_UNITS = {
    'english': [
        {"title": "Alphabet and Sounds", "steps": [
            {"prompt": "Let's start with the English alphabet. This is the letter A. Please say 'A'."},
            {"prompt": "This is the letter B. Please say 'B'."},
            {"prompt": "This is the letter C. Please say 'C'."},
            {"prompt": "This is the letter D. Please say 'D'."},
            {"prompt": "This is the letter E. Please say 'E'."},
            {"prompt": "This is the letter F. Please say 'F'."},
            {"prompt": "This is the letter G. Please say 'G'."},
            {"prompt": "This is the letter H. Please say 'H'."},
            {"prompt": "This is the letter I. Please say 'I'."},
            {"prompt": "This is the letter J. Please say 'J'."},
            {"prompt": "This is the letter K. Please say 'K'."},
            {"prompt": "This is the letter L. Please say 'L'."},
            {"prompt": "This is the letter M. Please say 'M'."},
            {"prompt": "This is the letter N. Please say 'N'."},
            {"prompt": "This is the letter O. Please say 'O'."},
            {"prompt": "This is the letter P. Please say 'P'."},
            {"prompt": "This is the letter Q. Please say 'Q'."},
            {"prompt": "This is the letter R. Please say 'R'."},
            {"prompt": "This is the letter S. Please say 'S'."},
            {"prompt": "This is the letter T. Please say 'T'."},
            {"prompt": "This is the letter U. Please say 'U'."},
            {"prompt": "This is the letter V. Please say 'V'."},
            {"prompt": "This is the letter W. Please say 'W'."},
            {"prompt": "This is the letter X. Please say 'X'."},
            {"prompt": "This is the letter Y. Please say 'Y'."},
            {"prompt": "This is the letter Z. Please say 'Z'."},
            {"prompt": "Great! Now let's move to basic words."}
        ]},
        {"title": "Basic Words (Nouns)", "steps": [
            {"prompt": "Say: 'cat'."},
            {"prompt": "Say: 'dog'."},
            {"prompt": "Say: 'apple'."},
            {"prompt": "Say: 'chair'."},
            {"prompt": "Say: 'This is a cat.'"},
            {"prompt": "Say: 'This is a dog.'"},
            {"prompt": "Great! Now let's move to verbs."}
        ]},
        {"title": "Verbs (Action Words)", "steps": [
            {"prompt": "Say: 'I eat.'"},
            {"prompt": "Say: 'You run.'"},
            {"prompt": "Say: 'We walk.'"},
            {"prompt": "Say: 'They come.'"},
            {"prompt": "Say: 'He goes.'"},
            {"prompt": "Great! Now let's make simple sentences."}
        ]},
        {"title": "Making Simple Sentences (Present Tense)", "steps": [
            {"prompt": "Say: 'I go to school.'"},
            {"prompt": "Say: 'He plays football.'"},
            {"prompt": "Say: 'She reads a book.'"},
            {"prompt": "Speak about your daily activities. For example: 'I wake up', 'I go to school'."},
            {"prompt": "Congratulations! You finished the English basics!"}
        ]},
        {"title": "Listening & Speaking Practice", "steps": [
            {"prompt": "Now, let's have a free conversation! Say anything in English and I will help you with corrections and suggestions."}
        ]}
    ],
    'hindi': [
        {"title": "हिंदी वर्णमाला और ध्वनियां", "steps": [
            {"prompt": "चलिए हिंदी वर्णमाला से शुरू करते हैं। यह अक्षर 'अ' है। कृपया 'अ' बोलें।"},
            {"prompt": "यह अक्षर 'आ' है। कृपया 'आ' बोलें।"},
            {"prompt": "यह अक्षर 'इ' है। कृपया 'इ' बोलें।"},
            {"prompt": "यह अक्षर 'ई' है। कृपया 'ई' बोलें।"},
            {"prompt": "यह अक्षर 'उ' है। कृपया 'उ' बोलें।"},
            {"prompt": "यह अक्षर 'ऊ' है। कृपया 'ऊ' बोलें।"},
            {"prompt": "यह अक्षर 'ए' है। कृपया 'ए' बोलें।"},
            {"prompt": "यह अक्षर 'ऐ' है। कृपया 'ऐ' बोलें।"},
            {"prompt": "यह अक्षर 'ओ' है। कृपया 'ओ' बोलें।"},
            {"prompt": "यह अक्षर 'औ' है। कृपया 'औ' बोलें।"},
            {"prompt": "यह अक्षर 'क' है। कृपया 'क' बोलें।"},
            {"prompt": "यह अक्षर 'ख' है। कृपया 'ख' बोलें।"},
            {"prompt": "यह अक्षर 'ग' है। कृपया 'ग' बोलें।"},
            {"prompt": "यह अक्षर 'घ' है। कृपया 'घ' बोलें।"},
            {"prompt": "यह अक्षर 'ङ' है। कृपया 'ङ' बोलें।"},
            {"prompt": "बहुत अच्छा! अब बुनियादी शब्दों की ओर बढ़ते हैं।"}
        ]},
        {"title": "बुनियादी शब्द (संज्ञाएं)", "steps": [
            {"prompt": "बोलें: 'पानी'।"},
            {"prompt": "बोलें: 'रोटी'।"},
            {"prompt": "बोलें: 'किताब'।"},
            {"prompt": "बोलें: 'घर'।"},
            {"prompt": "बोलें: 'यह पानी है।'"},
            {"prompt": "बोलें: 'यह रोटी है।'"},
            {"prompt": "बहुत अच्छा! अब क्रियाओं की ओर बढ़ते हैं।"}
        ]},
        {"title": "क्रियाएं (काम के शब्द)", "steps": [
            {"prompt": "बोलें: 'मैं खाता हूं।'"},
            {"prompt": "बोलें: 'तुम चलते हो।'"},
            {"prompt": "बोलें: 'हम सोते हैं।'"},
            {"prompt": "बोलें: 'वे आते हैं।'"},
            {"prompt": "बोलें: 'वह जाता है।'"},
            {"prompt": "बहुत अच्छा! अब सरल वाक्य बनाते हैं।"}
        ]},
        {"title": "सरल वाक्य बनाना (वर्तमान काल)", "steps": [
            {"prompt": "बोलें: 'मैं स्कूल जाता हूं।'"},
            {"prompt": "बोलें: 'वह फुटबॉल खेलता है।'"},
            {"prompt": "बोलें: 'वह किताब पढ़ती है।'"},
            {"prompt": "अपनी दैनिक गतिविधियों के बारे में बोलें। उदाहरण: 'मैं सुबह उठता हूं', 'मैं स्कूल जाता हूं'।"},
            {"prompt": "बधाई हो! आपने हिंदी के मूल सिद्धांत पूरे कर लिए हैं!"}
        ]},
        {"title": "सुनने और बोलने का अभ्यास", "steps": [
            {"prompt": "Now, let's have a free conversation! Say anything in English and I will help you with corrections and suggestions."}
        ]}
    ]
}

def gtts_tts(text, language='english'):
    try:
        lang_code = GTTS_LANG_CODES.get(language, 'en')
        tts = gTTS(text=text, lang=lang_code)
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        tts.save(filepath)
        return f"/static/audio/{filename}"
    except Exception as e:
        print("gTTS error:", e)
        return None

def get_groq_response(user_input, language='english'):
    if language == 'hindi':
        system_prompt = (
            "आप एक मित्रवत, प्रोत्साहन देने वाले हिंदी भाषा शिक्षक हैं। "
            "उपयोगकर्ता के वाक्य का विश्लेषण करें, प्रतिक्रिया दें, सुधार करें और प्रोत्साहन दें। "
            "यदि वाक्य अच्छा है, तो उपयोगकर्ता की प्रशंसा करें। यदि गलतियां हैं, तो धीरे से सुधार करें और समझाएं। "
            "अपनी प्रतिक्रिया छोटी और प्रेरणादायक रखें।"
        )
    else:
        system_prompt = (
            "You are a friendly, encouraging spoken English tutor. "
            "Analyze the user's sentence, give feedback, corrections, and encouragement. "
            "If the sentence is good, praise the user. If there are mistakes, gently correct them and explain. "
            "Keep your reply short and motivating."
        )
    
    try:
        result = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        reply = result.choices[0].message.content.strip()
        return reply
    except Exception as e:
        print("Groq error:", e)
        if language == 'hindi':
            return "क्षमा करें, मैं इसे संसाधित नहीं कर सका।"
        else:
            return "Sorry, I couldn't process that."

def is_answer_correct(user_input, expected_prompt):
    match = re.search(r"'([^']+)'", expected_prompt)
    if match:
        expected = match.group(1).lower()
        return expected in user_input.lower()
    # If no quoted phrase, always return True (move on)
    return True

# ========== INTERVIEW FUNCTIONS ==========
def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    try:
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.replace(".webm", ".wav")
        audio.export(wav_path, format="wav")
        
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data)
        print(f"📝 STT Result: {text}")
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that."
    except sr.RequestError as e:
        return f"STT request error: {e}"
    except Exception as e:
        print(f"❌ Error in speech_to_text: {e}")
        return "Sorry, I couldn't process the audio."

def get_groq_interview_reply(user_input):
    try:
        result = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a friendly spoken English teacher. Give grammar-focused spoken tasks. "
                        "Correct the user's speech politely, praise improvements, and increase difficulty step-by-step."
                    )
                },
                {"role": "user", "content": user_input}
            ],
            temperature=0.6
        )
        reply = result.choices[0].message.content.strip()
        print(f"🤖 Groq Reply: {reply}")
        return reply
    except Exception as e:
        return f"Error from Groq: {e}"

# ========== GRAMMAI CHATBOT ==========
chat_history = []

def generate_voice(text):
    try:
        print(f"\n🎤 Generating voice for: {text}")
        # Use gTTS with proper language code
        audio_url = gtts_tts(text, 'english')
        print(f"✅ Audio URL: {audio_url}")
        return audio_url
    except Exception as e:
        print("❌ Error in generate_voice():", e)
        return None

def get_groq_chat_response(user_input):
    try:
        # Add new user input to history
        chat_history.append({"role": "user", "content": user_input})
        
        # Format history as Groq expects: system + all previous user/assistant messages
        messages = [{"role": "system", "content": "You are Grammai, a friendly, talkative, and natural conversational partner. Speak like a real person, ask follow-up questions, share small talk, and avoid listing your features or sounding like a support agent. Keep the conversation flowing naturally, and be warm, casual, and engaging. Do not introduce yourself or explain your abilities. Just talk like a human friend."}]
        for entry in chat_history:
            role = "assistant" if entry["role"] == "groq" else entry["role"]
            messages.append({"role": role, "content": entry["content"]})

        result = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.85
        )
        reply = result.choices[0].message.content.strip()
        chat_history.append({"role": "groq", "content": reply})  # Save the bot's reply
        return reply
    except Exception as e:
        print("❌ Groq error:", e)
        return "Sorry, I couldn't process that."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/language-training')
def language_training():
    return render_template('language_training.html')

@app.route('/language-training/api', methods=['POST'])
def language_training_api():
    data = request.json
    language = data.get('language', 'english').lower()
    user_input = data.get('user_input', '').strip()
    custom_unit = data.get('unit', None)
    custom_step = data.get('step', None)
    
    print(f"🔍 Language Training API - Language: {language}, User input: '{user_input}', Custom unit: {custom_unit}, Custom step: {custom_step}")
    
    # Reset session when language changes or when custom unit/step is provided
    if 'lt_language' not in session or session['lt_language'] != language:
        session['lt_language'] = language
        session['lt_unit'] = int(custom_unit) if custom_unit is not None else 0
        session['lt_step'] = int(custom_step) if custom_step is not None else 0
        session['free_convo'] = False
        print(f"🔄 Session reset - New language: {language}, Unit: {session['lt_unit']}, Step: {session['lt_step']}")
    elif custom_unit is not None or custom_step is not None:
        # If custom unit/step is provided, reset to those values
        session['lt_unit'] = int(custom_unit) if custom_unit is not None else 0
        session['lt_step'] = int(custom_step) if custom_step is not None else 0
        session['free_convo'] = False
        print(f"🔄 Custom reset - Unit: {session['lt_unit']}, Step: {session['lt_step']}")
    
    units = LANGUAGE_UNITS.get(language, LANGUAGE_UNITS['english'])
    print(f"📚 Using units for language: {language}, Available units: {len(units)}")
    
    # Always use session for unit/step
    unit = session.get('lt_unit', 0)
    step = session.get('lt_step', 0)
    free_convo = session.get('free_convo', False)
    
    print(f"📍 Current position - Unit: {unit}, Step: {step}, Free convo: {free_convo}")
    
    # Safety check: reset if out of range
    if unit >= len(units):
        unit = 0
        session['lt_unit'] = 0
        print(f"⚠️ Unit out of range, resetting to 0")
    if step >= len(units[unit]['steps']):
        step = 0
        session['lt_step'] = 0
        print(f"⚠️ Step out of range, resetting to 0")
    
    unit_title = units[unit]['title']
    prompt = units[unit]['steps'][step]['prompt']
    
    print(f"📝 Current prompt - Unit: {unit_title}, Step prompt: {prompt}")
    
    # First load: greet and introduce unit
    if not user_input and not free_convo:
        greeting = f"Welcome! We are starting with {unit_title}. {prompt}"
        if language == 'hindi':
            greeting = f"स्वागत है! हम {unit_title} से शुरू कर रहे हैं। {prompt}"
        audio_url = gtts_tts(greeting, language)
        print(f"🎤 Generated greeting audio: {audio_url}")
        return jsonify({
            "unit_title": unit_title,
            "prompt": prompt,
            "audio": audio_url,
            "unit": unit,
            "step": step,
            "done": False,
            "user_input": "",
            "feedback": greeting,
            "free_convo": False
        })
    
    # Free conversation mode (last unit)
    if unit == len(units) - 1 or session.get('free_convo', False):
        session['free_convo'] = True
        if user_input.lower().strip() == 'reset':
            if custom_unit is not None:
                session['lt_unit'] = int(custom_unit)
            else:
                session['lt_unit'] = 0
            if custom_step is not None:
                session['lt_step'] = int(custom_step)
            else:
                session['lt_step'] = 0
            session['free_convo'] = False
            unit = session['lt_unit']
            step = session['lt_step']
            unit_title = units[unit]['title']
            prompt = units[unit]['steps'][step]['prompt']
            greeting = f"Reset! We are starting again with {unit_title}. {prompt}"
            audio_url = gtts_tts(greeting, language)
            return jsonify({
                "unit_title": unit_title,
                "prompt": prompt,
                "audio": audio_url,
                "unit": unit,
                "step": step,
                "done": False,
                "user_input": "",
                "feedback": greeting,
                "free_convo": False
            })
        feedback = get_groq_response(user_input, language)
        audio_url = gtts_tts(feedback, language)
        return jsonify({
            "unit_title": "Free Conversation",
            "prompt": "Say anything! The AI tutor will help you.",
            "audio": audio_url,
            "unit": unit,
            "step": step,
            "done": True,
            "user_input": user_input,
            "feedback": feedback,
            "free_convo": True
        })
    
    # If user input is not empty, always move forward
    if user_input:
        if step < len(units[unit]['steps']) - 1:
            feedback = "Great job!"
            session['lt_step'] = step + 1
            done = False
            # Get next prompt
            next_unit = session['lt_unit']
            next_step = session['lt_step']
            next_unit_title = units[next_unit]['title']
            next_prompt = units[next_unit]['steps'][next_step]['prompt']
            audio_text = f"{feedback} Next: {next_prompt}"
            audio_url = gtts_tts(audio_text, language)
            return jsonify({
                "unit_title": next_unit_title,
                "prompt": next_prompt,
                "audio": audio_url,
                "unit": next_unit,
                "step": next_step,
                "done": done,
                "user_input": user_input,
                "feedback": f"{feedback} Next: {next_prompt}",
                "free_convo": session['free_convo']
            })
        else:
            if unit < len(units) - 1:
                feedback = f"Awesome! 🎉 You finished {unit_title}."
                session['lt_unit'] = unit + 1
                session['lt_step'] = 0
                done = False
                # Get next unit's first prompt
                next_unit = session['lt_unit']
                next_step = session['lt_step']
                next_unit_title = units[next_unit]['title']
                next_prompt = units[next_unit]['steps'][next_step]['prompt']
                audio_text = f"{feedback} Next: {next_prompt}"
                audio_url = gtts_tts(audio_text, language)
                return jsonify({
                    "unit_title": next_unit_title,
                    "prompt": next_prompt,
                    "audio": audio_url,
                    "unit": next_unit,
                    "step": next_step,
                    "done": done,
                    "user_input": user_input,
                    "feedback": f"{feedback} Next: {next_prompt}",
                    "free_convo": session['free_convo']
                })
            else:
                feedback = "Congratulations! You finished all units! Now you can talk to me freely. Say anything, or say 'reset' to start again."
                session['free_convo'] = True
                done = True
                audio_text = feedback
                audio_url = gtts_tts(audio_text, language)
                return jsonify({
                    "unit_title": unit_title,
                    "prompt": prompt,
                    "audio": audio_url,
                    "unit": unit,
                    "step": step,
                    "done": done,
                    "user_input": user_input,
                    "feedback": feedback,
                    "free_convo": session['free_convo']
                })
    
    # If no user input, just repeat the prompt
    audio_url = gtts_tts(prompt, language)
    return jsonify({
        "unit_title": unit_title,
        "prompt": prompt,
        "audio": audio_url,
        "unit": unit,
        "step": step,
        "done": False,
        "user_input": user_input,
        "feedback": "",
        "free_convo": False
    })

@app.route('/language-training/image', methods=['POST'])
def language_training_image():
    language = request.form.get('language', 'english').lower()
    file = request.files.get('image')
    if not file:
        return jsonify({"error": "No image uploaded."}), 400
    filename = f"img_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(AUDIO_DIR, filename)
    file.save(filepath)
    # Google Cloud Vision API
    try:
        client = vision.ImageAnnotatorClient()
        with open(filepath, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.label_detection(image=image)
        labels = response.label_annotations
        if labels:
            label = labels[0].description
            description = f"This is a {label}."
        else:
            label = None
            description = "Sorry, I couldn't confidently recognize the image. Try a clearer object or a different image."
    except Exception as e:
        print("Vision API error:", e)
        label = None
        description = "Sorry, I couldn't analyze the image."
    audio_url = gtts_tts(description, language)
    return jsonify({"label": label, "description": description, "audio": audio_url})

@app.route('/interview')
def interview():
    return render_template('interview.html', chat_history=chat_history)

@app.route('/interview/chat', methods=['POST'])
def interview_chat():
    user_input = request.form.get("user_input", "").strip()
    print(f"\n📥 Received input: {user_input}")
    if not user_input:
        return jsonify(reply="", audio=None)

    reply = get_groq_chat_response(user_input)
    audio_url = generate_voice(reply)
    print(f"🔗 Streaming audio from: {audio_url}")

    return jsonify(reply=reply, audio=audio_url)

@app.route('/interview/reset')
def interview_reset():
    global chat_history
    chat_history = []
    return render_template('interview.html', chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True) 