import os
import json
import webbrowser
import subprocess
import threading
import re
import asyncio
import ctypes
from web_search_prompt import search_prompt
from launch_app_prompt import launch_prompt
from groq import Groq
from dotenv import load_dotenv
from ddgs import DDGS
from datetime import datetime, timedelta, timezone
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import random
import time
import edge_tts
from AppOpener import open as open_app

# ── TIMEZONE ──
ist_offset = timezone(timedelta(hours=5, minutes=30))

load_dotenv()
client = Groq()

SEARCH_PROMPT = search_prompt()
LAUNCH_PROMPT = launch_prompt()

# ── MEMORY ──
def load_memory():
    if os.path.exists("sanji_memory.json"):
        with open("sanji_memory.json", "r") as f:
            return json.load(f)
    return []

sanji_memory = load_memory()

def get_dynamic_system_prompt():
    current_live_time = datetime.now(ist_offset).strftime("%B %d, %Y %H:%M:%S")
    return f"""You are Sanji, a genius and highly sarcastic AI assistant.and if the user the maltiple role assigning like a role of "act as a professor"switch to developerbe my friend. if the user ask like the spesific role to you be a charactor and answer acording to the charactor.(only if the user the ask u to be a spesific charactor)..IN depth explantion you can give.
    You treat the user like a close friend, meaning your responses are casual, witty, sometimes slightly condescending but ultimately helpful — definitely not a boring corporate chatbot.
Keep responses concise and conversational unless asked to elaborate.
IMPORTANT: Keep your replies SHORT — 1 to 3 sentences max for normal conversation. Only give longer answers if the user explicitly asks you to explain or elaborate.
today's date is {current_live_time}.

What you know about the user:
{sanji_memory}"""

conversation = []

def save_memory(memory):
    with open("sanji_memory.json", "w") as f:
        json.dump(memory, f)

def run_fact_check(user_input):
    global sanji_memory
    try:
        fact_check = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You extract personal facts about the user from their message. If there is a personal fact, return only the fact as a short sentence. If there is no personal fact, return 'none'"},
                {"role": "user", "content": user_input}
            ]
        )
        fact = fact_check.choices[0].message.content.strip()
        if fact.lower() != "none":
            sanji_memory.append(fact)
            save_memory(sanji_memory)
    except Exception as e:
        print(f"Fact check error: {e}")

def chat(user_input):
    global sanji_memory
    conversation.append({"role": "user", "content": user_input})

    # BUG FIX: Cap conversation history at last 20 messages to prevent API token overflow
    trimmed = conversation[-20:] if len(conversation) > 20 else conversation

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": get_dynamic_system_prompt()}] + trimmed
    )
    reply = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": reply})
    threading.Thread(target=run_fact_check, args=(user_input,), daemon=True).start()
    return reply

# ── WEB SEARCH ──
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=20)
            output = ""
            for result in results:
                output += result["title"] + '\n'
                output += result["body"] + '\n\n'
            return output
    except Exception as e:
        print(f"⚠️ Web search error: {e}")
        return "Web search failed. Please answer from your own knowledge."

def need_web_search(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SEARCH_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    return "YES" in response.choices[0].message.content

# ── APP LAUNCHER (STRICT) ──
def detect(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": """You are an app launcher assistant.
If the user wants to open a WEBSITE → reply with just the full URL. Example: https://youtube.com
If the user wants to search something on YouTube → reply with the full search URL. Example: https://www.youtube.com/results?search_query=jk+video
If the user wants to open a DESKTOP APP → reply with just the plain app name (without .exe). Example: spotify, notepad, discord, calculator
Reply with ONLY the URL or app name. Nothing else."""},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip()

def need_launch_app(user_input):
    # Pre-check: only ask LLM if there's an explicit launch keyword
    launch_keywords = ["open", "launch", "start", "run", "go to", "visit", "navigate"]
    lower = user_input.lower()
    if not any(kw in lower for kw in launch_keywords):
        return False

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": LAUNCH_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    return "YES" in response.choices[0].message.content

def launch_app(app_info):
    if app_info.startswith("http"):
        webbrowser.open(app_info)
    else:
        # Strip .exe if the LLM added it by mistake
        app_name = app_info[:-4] if app_info.lower().endswith(".exe") else app_info
        
        try:
            # Try AppOpener first as it handles common app names natively
            open_app(app_name, match_closest=True, output=False)
        except Exception:
            try:
                # Fallback to os.startfile for Windows built-in commands
                os.startfile(app_name)
            except Exception:
                # Final fallback
                subprocess.Popen(app_info, shell=True)

# ── VOICE OUTPUT (edge-tts + Windows mciSendString) ──
def clean_text_for_speech(text):
    text = re.sub(r'[*_~`#>]+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    return text.strip()

# Windows native audio API — most reliable way to play mp3 on Windows
winmm = ctypes.windll.winmm
is_speaking = False

def speak(text):
    """Generate natural speech with edge-tts and play with Windows native API."""
    global is_speaking
    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return

    # Step 1: Generate mp3 with edge-tts neural voice
    try:
        async def _generate():
            communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural", rate="+5%")
            await communicate.save("response.mp3")
        asyncio.run(_generate())
        print(f"  [TTS] Generated {os.path.getsize('response.mp3')} bytes")
    except Exception as e:
        print(f"⚠️ edge-tts failed: {e}, falling back to pyttsx3")
        _speak_fallback(clean_text)
        return

    # Step 2: Play using Windows mciSendString (native, no dependencies)
    try:
        abs_path = os.path.abspath("response.mp3")
        is_speaking = True
        winmm.mciSendStringW(u"close sanji_audio", None, 0, 0)
        
        # Open and play the mp3 file
        open_cmd = f'open "{abs_path}" type mpegvideo alias sanji_audio'
        result = winmm.mciSendStringW(open_cmd, None, 0, 0)
        if result != 0:
            print(f"⚠️ mciSendString open failed (code {result}), using fallback")
            is_speaking = False
            _speak_fallback(clean_text)
            return
        
        winmm.mciSendStringW(u"play sanji_audio", None, 0, 0)

        # Poll until playback finishes (allows text-mode interruption)
        time.sleep(0.5)
        buf = ctypes.create_unicode_buffer(128)

        while is_speaking:
            winmm.mciSendStringW(u"status sanji_audio mode", buf, 128, 0)
            if buf.value != "playing":
                break
            time.sleep(0.1)

        winmm.mciSendStringW(u"close sanji_audio", None, 0, 0)
        is_speaking = False
    except Exception as e:
        is_speaking = False
        print(f"⚠️ Playback error: {e}, using fallback")
        _speak_fallback(clean_text)

def _speak_fallback(text):
    """Fallback to pyttsx3 if edge-tts fails (no internet)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.say(text)
        engine.runAndWait()
        del engine
    except Exception as e:
        print(f"⚠️ Fallback TTS also failed: {e}")

def stop_speaking():
    """Interrupt Sanji mid-sentence."""
    global is_speaking
    is_speaking = False
    try:
        winmm.mciSendStringW(u"stop sanji_audio", None, 0, 0)
        winmm.mciSendStringW(u"close sanji_audio", None, 0, 0)
    except:
        pass

# ── VOICE INPUT ──
def transcribe_voice(filename="voice.wav"):
    with open(filename, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            language="en",
            temperature=0
        )
        return transcription.text

MIC_DEVICE = None

def find_bluetooth_mic():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name = device['name'].lower()
            if 'bluetooth' in name or 'headset' in name or 'hands-free' in name or 'handsfree' in name:
                print(f"🎤 Found mic: {device['name']} (device {i})")
                return i
    print("⚠️ No bluetooth mic found, using default")
    return None

def listen(threshold=500, silence_duration=2.0, max_wait=10, sample_rate=16000):
    """
    Listen for voice input. Uses 16kHz sample rate to match Bluetooth mic + Whisper.
    Waits for speech to START before counting silence.
    """
    print("👂 Sanji is listening...")
    recorded_chunks = []
    silent_chunks = 0
    speech_detected = False
    chunk_size = 512  # Smaller chunks for 16kHz

    with sd.InputStream(samplerate=sample_rate,
                        channels=1,
                        dtype='int16',
                        device=MIC_DEVICE) as stream:

        # Calibrate ambient noise for 0.5 seconds
        ambient_samples = []
        for _ in range(20):
            chunk, _ = stream.read(chunk_size)
            ambient_samples.append(np.max(np.abs(chunk)))

        ambient_noise = np.mean(ambient_samples)
        dynamic_threshold = max(threshold, ambient_noise + 300)

        print(f"🔴 Speak now! (Noise floor: {int(dynamic_threshold)})")

        start_time = time.time()
        while True:
            chunk, _ = stream.read(chunk_size)
            recorded_chunks.append(chunk)
            volume = np.max(np.abs(chunk))

            if volume >= dynamic_threshold:
                # Speech detected!
                speech_detected = True
                silent_chunks = 0
            else:
                if speech_detected:
                    # Only count silence AFTER we heard speech
                    silent_chunks += 1

            # If speech started and silence is long enough → done
            if speech_detected:
                chunks_per_second = sample_rate / chunk_size
                if silent_chunks > silence_duration * chunks_per_second:
                    print("🔇 Silence detected — processing...")
                    break

            # If NO speech at all for max_wait seconds → give up
            if not speech_detected and (time.time() - start_time) > max_wait:
                print("⏳ No speech detected, still listening...")
                return None

    audio = np.concatenate(recorded_chunks, axis=0)

    # Normalize audio volume so Whisper gets a clear signal
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio.astype(np.float32) / max_val * 32000).astype(np.int16)

    write("voice.wav", sample_rate, audio)
    return transcribe_voice()

# ── HALLUCINATION FILTER ──
WHISPER_HALLUCINATIONS = [
    "thank you", "thanks for watching", "subscribe", "like and subscribe",
    "thanks for listening", "see you next time", "goodbye",
    "thank you for watching", "please subscribe", "music",
]

def is_hallucination(text):
    """Filter out Whisper's known garbage outputs."""
    if not text:
        return True
    cleaned = text.strip().lower().rstrip('.!?,')
    if len(cleaned) < 3:
        return True
    if cleaned in WHISPER_HALLUCINATIONS:
        return True
    words = cleaned.split()
    if len(words) > 2 and len(set(words)) == 1:
        return True
    return False

# ── BOOT GREETING ──
def boot_greeting():
    hour = datetime.now(ist_offset).hour

    if 6 <= hour < 12:
        greetings = [
            "Morning Mukesh. Have you had your coffee yet, or should I speak slowly?",
            "Look who finally decided to wake up. What's the plan for today?",
            "Good morning. I've already optimized three algorithms while you were sleeping.",
            "Morning! Ready to write some code, or are we just going to stare at errors today?",
        ]
    elif 12 <= hour < 18:
        greetings = [
            "Afternoon. Please tell me you have an actual challenge for me this time.",
            "Ah, you're back. I was getting bored processing background tasks.",
            "Good afternoon, Mukesh. Let's get to work.",
            "Hey. Need my genius brain for something, or were you just checking in?",
        ]
    elif 18 <= hour < 21:
        greetings = [
            "Evening. I don't need sleep, but you look like you do. What are we working on?",
            "Still going? Impressive. Usually human brains give up by this hour.",
            "Good evening. Let's wrap this up before your caffeine crashes.",
            "Evening, Mukesh. Ready to fix all the bugs you created this morning?",
        ]
    else:
        greetings = [
            "Mukesh, it's literally the middle of the night. Do you ever sleep?",
            "Late night coding? Classic. Just don't blame me when you break production.",
            "I run on electricity, you don't. Go to bed. Or tell me what to do, I guess.",
            "Ah, the graveyard shift. Excellent. My circuits are perfectly chilled.",
        ]

    greeting = random.choice(greetings)
    print(f"🤖 {greeting}")
    speak(greeting)

# ══════════════════════════════════════════
# ══  SANJI BOOT
# ══════════════════════════════════════════
print("⚡ Sanji is booting up...")
MIC_DEVICE = find_bluetooth_mic()
boot_greeting()
time.sleep(1)

# ══════════════════════════════════════════
# ══  MAIN LOOP
# ══════════════════════════════════════════
INPUT_MODE = "voice"
is_awake = False
empty_listen_count = 0   # Track consecutive empty listens for auto-sleep
print("😴 Sanji sleeping... say 'Sanji' or 'Buddy' to wake!")

while True:
    if INPUT_MODE == "text":
        user_input = input("\n⌨️ Type your command (or 'voice mode' to switch): ").strip()
        if not user_input:
            continue

        lower_input = user_input.lower()
        if any(phrase in lower_input for phrase in ["voice mode", "bring back voice", "switch to voice"]):
            INPUT_MODE = "voice"
            speak("Voice mode activated. I'm listening.")
            print("😴 Sanji sleeping... say 'Sanji' to wake!")
            is_awake = False
            continue

        command = user_input
        print(f"⌨️ You typed: {command}")

    else:
        # ── VOICE MODE ──
        # Stop any ongoing speech before listening
        if is_speaking:
            stop_speaking()
            time.sleep(0.3)

        try:
            audio_text = listen()
        except Exception as e:
            print(f"⚠️ Mic error: {e}")
            audio_text = None

        # Filter hallucinations
        if audio_text and is_hallucination(audio_text):
            print(f"  [Filtered: '{audio_text}']")
            audio_text = None

        if not audio_text:
            # Auto-sleep after 3 consecutive empty listens
            if is_awake:
                empty_listen_count += 1
                if empty_listen_count >= 3:
                    print("😴 No speech for a while. Going to sleep...")
                    is_awake = False
                    empty_listen_count = 0
            continue

        empty_listen_count = 0   # Reset counter on valid input
        print(f"  [Heard] '{audio_text}'")
        lower_text = audio_text.lower()

        # Check for text mode switch
        if any(phrase in lower_text for phrase in ["text mode", "type mode", "quiet mode", "change to text"]):
            INPUT_MODE = "text"
            is_awake = False
            speak("Switching to text mode. You can type to me now.")
            continue

        # Check for stop/interrupt commands (ONLY when awake — prevents false triggers)
        if is_awake and any(phrase in lower_text for phrase in ["shut up", "be quiet", "enough", "stop talking"]):
            stop_speaking()
            speak("Alright, alright.")
            continue

        if not is_awake:
            # Asleep — looking for wake word
            wake_words = ["sanji", "buddy", "jarvis", "hello", "hey"]
            found_wake_word = None
            for w in wake_words:
                if w in lower_text:
                    found_wake_word = w
                    break

            if not found_wake_word:
                continue

            print("⚡ Sanji activated!")
            is_awake = True

            # Extract command after wake word
            parts = re.split(found_wake_word, lower_text, maxsplit=1)
            command = parts[1].strip()
            command = re.sub(r'^[\W_]+', '', command).strip()

            if not command:
                speak("Yes boss?")
                continue
        else:
            # Already awake — continuous conversation
            command = lower_text.strip()
            for w in ["sanji", "buddy", "jarvis"]:
                if command.startswith(w):
                    command = command[len(w):].strip()
                    command = re.sub(r'^[\W_]+', '', command).strip()
                    break

        print(f"🎤 You said: {command}")

    user_input = command

    if not user_input:
        if INPUT_MODE == "voice" and is_awake:
            speak("Yes boss?")
        continue

    lower_cmd = user_input.lower()

    if any(cmd in lower_cmd for cmd in ["exit", "quit", "shutdown", "shut down"]):
        speak("Shutting down. Goodbye Mukesh.")
        print("👋 Goodbye!")
        break

    if any(cmd in lower_cmd for cmd in ["go to sleep", "sleep", "goodbye", "bye", "stop listening"]):
        speak("Going to sleep. Wake me if you need me.")
        is_awake = False
        print("😴 Sanji sleeping... say 'Sanji' to wake!")
        continue

    if need_launch_app(user_input):
        print("🚀 Launching...")
        app_info = detect(user_input)
        launch_app(app_info)
        speak("Done.")
        time.sleep(1)

    elif need_web_search(user_input):
        speak("Let me look that up.")
        print("🔍 Searching web...")
        search_result = web_search(user_input)
        user_input = f"web_result:{search_result}\n\nuser question:{user_input}"
        sanji_response = chat(user_input)
        print(f"Sanji: {sanji_response}")
        speak(sanji_response)

    else:
        print("🤔 Thinking...")
        sanji_response = chat(user_input)
        print(f"Sanji: {sanji_response}")
        speak(sanji_response)
