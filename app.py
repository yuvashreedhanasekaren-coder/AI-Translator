from pydoc import text
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator, MyMemoryTranslator
import os
import sys
import sqlite3
import random
import re
import uuid
import subprocess
import threading
import queue
import cv2
import numpy as np
import pytesseract
import librosa
import whisper
import torch
from gtts import gTTS 
import sounddevice as sd
from PIL import Image, ImageOps
from flask_mail import Mail, Message
from yt_dlp import YoutubeDL
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

video_jobs = {}

print("Loading Whisper model once...")
from faster_whisper import WhisperModel

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)
print("Whisper model loaded successfully!")

# FAST TRANSLATOR CACHE
translator_cache = {}

print("Running Python:", sys.executable)

# ---------- APP ----------
app = Flask(__name__)
app.secret_key = "secret123"

# ---------- TESSERACT ----------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- UPLOAD CONFIG ----------  
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads") 
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- DATABASE ----------
DATABASE = "database.db"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        purpose TEXT,
        is_verified INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        is_deleted INTEGER DEFAULT 0,
        otp TEXT
    )
    """)

    # Add purpose column to existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN purpose TEXT")
    except sqlite3.OperationalError:
        pass

    # Add is_admin column to existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Add is_deleted column to existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_deleted INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Rebuild users table to allow deleted email/username reuse
    cursor.execute("""
        SELECT sql
        FROM sqlite_master
        WHERE type='table' AND name='users'
    """)

    users_table_sql = cursor.fetchone()[0] or ""

    if "username TEXT UNIQUE" in users_table_sql or "email TEXT UNIQUE" in users_table_sql:

        cursor.execute("""
            CREATE TABLE users_new(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT,
                password TEXT,
                purpose TEXT,
                is_verified INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_deleted INTEGER DEFAULT 0,
                otp TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO users_new
            (id, username, email, password, purpose,
            is_verified, is_admin, is_deleted, otp)
            SELECT id, username, email, password, purpose,
                is_verified, is_admin, is_deleted, otp
            FROM users
        """)

        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

    # Allow only active users to have unique email and username
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_active_email
        ON users(email)
        WHERE is_deleted = 0
    """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_active_username
        ON users(username)
        WHERE is_deleted = 0
    """)    

    conn.commit()
    conn.close()

init_db()

# ---------- PASSWORD CHECK ----------
def strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    return re.match(pattern, password)

# ---------- MAIL CONFIG ----------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "yuvashreesince2004@gmail.com"
app.config['MAIL_PASSWORD'] = "abwkxjhrzezwdqom"
app.config['MAIL_DEFAULT_SENDER'] = "yuvashreesince2004@gmail.com"

mail = Mail(app)

def send_otp_email(email, otp):
    try:
        msg = Message(
            subject="Your OTP Verification Code",
            recipients=[email]
        )
        msg.body = f"""
Hello,

Your OTP code is: {otp}

Do not share this with anyone.

Thank you.
"""
        mail.send(msg)
        print("OTP sent successfully to", email)

    except Exception as e:
        print("Mail sending error:", e)

# ---------- ISTER ----------
@app.route("/")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        purpose = request.form["purpose"]

        db = get_db()

        # Check existing active user
        existing = db.execute(
            """
            SELECT * FROM users
            WHERE (email=? OR username=?)
            AND is_deleted=0
            """,
            (email, username)
        ).fetchone()

        if existing:        
            return render_template("already_account.html")

        if existing:
            return render_template("already_account.html")

        otp = str(random.randint(100000,999999))

        db.execute("""
    INSERT INTO users(username,email,password,purpose,otp,is_verified)
    VALUES (?,?,?,?,?,0)
""",(
    username,
    email,
    generate_password_hash(password),
    purpose,
    otp
))
        db.commit()

        send_otp_email(email, otp)

        return redirect(url_for("verify_otp", email=email))

    return render_template("register.html")

#  --------------- verify OTP ----------------
@app.route("/verify_otp", methods=["GET","POST"])
def verify_otp():

    email = request.args.get("email")

    if request.args.get("skip") == "1":
        return redirect(url_for("login"))

    if request.method == "POST":

        entered_otp = request.form["otp"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and user["otp"] == entered_otp:

            db.execute("""
                UPDATE users
                SET is_verified=1, otp=NULL
                WHERE email=?
            """,(email,))
            db.commit()

            return redirect(url_for("login"))

        else:
            return "Wrong OTP!"

    return render_template("verify_otp.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        # Check active user first
        user = db.execute(
            """
            SELECT * FROM users
            WHERE username=? AND is_deleted=0
            """,
            (username,)
        ).fetchone()

        if not user:
            # Check whether this username belongs to a deleted account
            deleted_user = db.execute(
                """
                SELECT * FROM users
                WHERE username=? AND is_deleted=1
                """,
                (username,)
            ).fetchone()

            if deleted_user:
                return render_template(
                    "login.html",
                    error="Your account has been deleted. Please register again to create a new account."
                )

            return render_template(
                "login.html",
                error="User not found"
            )

        if not check_password_hash(user["password"], password):
            return render_template(
                "login.html",
                error="Wrong password"
            )

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user["is_admin"])

        return redirect(url_for("home"))

    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("register_page"))

# ---------- FORGOT PASSWORD ----------
@app.route("/forgot_page")
def forgot_page():
    return render_template("forgot.html")

@app.route("/forgot", methods=["GET","POST"])
def forgot():

    if request.method == "POST":
        email = request.form["email"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user:
            otp = str(random.randint(100000,999999))

            db.execute("""
                UPDATE users SET otp=? WHERE email=?
            """,(otp,email))
            db.commit()

            send_otp_email(email, otp)

            return redirect(url_for("verify_reset_otp", email=email))

        else:
            return "Email not found!"

    return render_template("forgot.html")

# ---------- VERIFY OTP ----------
@app.route("/verify_reset_otp", methods=["GET","POST"])
def verify_reset_otp():

    email = request.args.get("email")

    if request.method == "POST":

        entered_otp = request.form["otp"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and user["otp"] == entered_otp:
            return redirect(url_for("reset_password", email=email))

        else:
            return "Wrong OTP!"

    return render_template("verify_reset_otp.html")

# ---------- RESET PASSWORD ----------
@app.route("/reset_password", methods=["GET","POST"])
def reset_password():

    email = request.args.get("email")

    if request.method == "POST":

        new_password = request.form["password"]

        db = get_db()
        db.execute("""
            UPDATE users
            SET password=?, otp=NULL
            WHERE email=?
        """,(generate_password_hash(new_password), email))

        db.commit()

        return redirect(url_for("login"))

    return render_template("reset_password.html")


# ---------- IMAGE OCR + TRANSLATION ----------

@app.route("/image", methods=["GET", "POST"])
def image_page():

    if request.method == "GET":
        return render_template("image.html")

    file = request.files.get("image")
    target_lang = request.form.get("target_lang", "ta").strip().lower()

    supported_languages = {
        "ta": "Tamil",
        "en": "English",
        "te": "Telugu",
        "kn": "Kannada"
    }

    # Validate output language
    if target_lang not in supported_languages:
        return render_template(
            "image.html",
            error="Please select a valid output language."
        )

    # Validate uploaded image
    if not file or not file.filename:
        return render_template(
            "image.html",
            error="Please select an image."
        )

    filename = secure_filename(file.filename)

    if not filename:
        return render_template(
            "image.html",
            error="Invalid image filename."
        )

    upload_folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    path = os.path.join(upload_folder, filename)

    try:
        # Save the image
        file.save(path)

        # Open image and correct its orientation
        with Image.open(path) as original:
            img = ImageOps.exif_transpose(original).convert("RGB")

        # Convert to OpenCV format
        img_cv = cv2.cvtColor(
            np.array(img),
            cv2.COLOR_RGB2BGR
        )

        # Grayscale preprocessing
        gray = cv2.cvtColor(
            img_cv,
            cv2.COLOR_BGR2GRAY
        )

        # Enlarge smaller images
        if gray.shape[0] < 1000:
            gray = cv2.resize(
                gray,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC
            )

        # Improve contrast
        thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        # OCR: English and Hindi
        extracted_text = pytesseract.image_to_string(
            thresh,
            lang="eng+hin",
            config="--psm 6"
        ).strip()

        print("OCR extracted text:", repr(extracted_text))

        if not extracted_text:
            return render_template(
                "image.html",
                error=(
                    "No English or Hindi text detected. "
                    "Try a clearer image."
                )
            )

        # Translate using the existing translation helper
        translated = hybrid_translate(
            extracted_text,
            target_lang
        )

        print(
            "Selected language:",
            supported_languages[target_lang]
        )
        print("Translation result:", repr(translated))

        if not translated or translated == "Translation failed":
            return render_template(
                "image.html",
                error=(
                    "Translation failed. Please check the "
                    "translation error in the terminal and try again."
                )
            )

        # Render the result page
        return render_template(
            "output.html",
            translated=translated,
            image_filename=filename,
            extracted_text=extracted_text
        )

    except Exception as e:
        app.logger.exception("IMAGE OCR OR TRANSLATION FAILED")

        return render_template(
            "image.html",
            error=f"Image translation failed: {str(e)}"
        ), 500


# ---------- SERVE UPLOADED FILE ----------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --------------- video translation ------------------

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"

def extract_audio(video_path, unique_id):

    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], f"audio_{unique_id}.wav")

    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path
    ]

    try:
        subprocess.run(command, check=True)
    except Exception as e:
        print("FFMPEG ERROR:", e)
        raise

    return audio_path

def download_youtube_video(url, unique_id):

    output_template = os.path.join(
        app.config["UPLOAD_FOLDER"], f"yt_input_{unique_id}.%(ext)s"
    )

    ydl_opts = {
    "format": "bestvideo+bestaudio/best",
    "outtmpl": output_template,
    "quiet": True,
    "noplaylist": True,

    "socket_timeout": 60,
    "retries": 10,
    "fragment_retries": 10,
    "retry_sleep": 5,
    "source_address": "0.0.0.0",

    "http_headers": {
        "User-Agent": "Mozilla/5.0"
    },

    # 🔥 USE THIS ONLY
    "cookiefile": "cookies.txt",

    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    return file_path

def generate_subtitles_and_audio(audio_path, target_lang, unique_id):
    import time
    import requests
    from deep_translator import GoogleTranslator

    print("🔥 Subtitle generation started")

    segments, info = whisper_model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    segments = list(segments)
    print("Segments detected:", len(segments))

    if not segments:
        raise RuntimeError("No speech detected in the uploaded video.")

    srt_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        f"subtitles_{unique_id}.srt"
    )
    translated_audio_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        f"translated_audio_{unique_id}.mp3"
    )

    translated_segments = []

    def translate_with_mymemory(text):
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": f"en|{target_lang}",
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") != 200:
            raise RuntimeError(
                data.get("responseDetails", "MyMemory translation failed")
            )

        result = (
            data.get("responseData", {})
            .get("translatedText", "")
            .strip()
        )

        if not result:
            raise RuntimeError("MyMemory returned empty translation.")

        return result

    for i, segment in enumerate(segments, start=1):
        original_text = segment.text.strip()

        if not original_text:
            translated_segments.append("...")
            continue

        print(f"Translating segment {i}/{len(segments)}: {original_text}")

        translated = None

        # Try Google Translate, with limited retries for rate limiting.
        for attempt in range(2):
            try:
                result = GoogleTranslator(
                    source="en",
                    target=target_lang
                ).translate(original_text)

                if result and result.strip():
                    translated = result.strip()
                    break

                raise RuntimeError("Google returned empty translation.")

            except Exception as error:
                print(
                    f"Google failed on segment {i}, "
                    f"attempt {attempt + 1}: {repr(error)}"
                )
                if attempt == 0:
                    time.sleep(2)

        # Fall back to MyMemory for this segment only.
        if translated is None:
            try:
                translated = translate_with_mymemory(original_text)
                print(f"✅ MyMemory translated segment {i}")
            except Exception as error:
                print(
                    f"MyMemory failed on segment {i}: {repr(error)}"
                )
                raise RuntimeError(
                    f"Could not translate subtitle segment {i}. "
                    "Please try again later."
                ) from error

        translated_segments.append(translated)
        time.sleep(0.5)

    translated_text_full = " ".join(translated_segments).strip()

    if not translated_text_full:
        raise RuntimeError("Translated text is empty.")

    # Write subtitles with the original segment timings.
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (segment, translated) in enumerate(
            zip(segments, translated_segments), start=1
        ):
            f.write(f"{i}\n")
            f.write(
                f"{format_time(segment.start)} --> "
                f"{format_time(segment.end)}\n"
            )
            f.write(f"{translated}\n\n")

    print("✅ SRT created at:", srt_path)

    # Generate target-language speech.
    try:
        tts = gTTS(
            text=translated_text_full,
            lang=target_lang
        )
        tts.save(translated_audio_path)

    except Exception as error:
        print("Target-language voice generation failed:", repr(error))
        raise RuntimeError(
            f"Could not generate voice for language: {target_lang}"
        ) from error

    print("✅ Translated audio created")
    return srt_path, translated_audio_path

def merge_all(video_path, audio_path, subtitle_path, unique_id):
    output_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        f"final_output_{unique_id}.mkv"
    )

    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-i", subtitle_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-map", "2:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-c:s", "srt",
        "-disposition:s:0", "default",
        output_path
    ]

    subprocess.run(command, check=True)
    print("✅ Video, translated audio and subtitles merged:", output_path)

    return output_path

# ------------------ FLASK ROUTES ------------------

@app.route("/video")
def video_options():
    return render_template("video_options.html")

@app.route("/recorded-video")
def recorded_video():
    return render_template("recorded_video.html")

@app.route("/youtube_translation", methods=["GET", "POST"])
def youtube_translation():

    if request.method == "POST":

        url = request.form["youtube_url"]
        language = request.form["language"]
        unique_id = str(uuid.uuid4())

        video_jobs[unique_id] = {
            "status": "processing",
            "output": None
        }

        thread = threading.Thread(
            target=process_video_job,
            args=(url, language, unique_id)
        )
        thread.start()

        return render_template(
    "status.html",
    job_id=unique_id
)

    return render_template("youtube_translation.html")

@app.route("/final_video/<job_id>")
def final_video(job_id):

    job = video_jobs.get(job_id)

    if not job:
        return "Invalid Job ID"

    if job["status"] != "completed":
        return redirect(url_for("video_status", job_id=job_id))

    return render_template(
        "video_output.html",
        translated_video=job["output"]
    )

def process_video_job(url, language, unique_id):
    try:
        print("⬇️ Downloading video...")
        video_jobs[unique_id]["status"] = "downloading"
        video_path = download_youtube_video(url, unique_id)

        print("🎧 Extracting audio...")
        video_jobs[unique_id]["status"] = "extracting_audio"
        audio_path = extract_audio(video_path, unique_id)

        print("🧠 Transcribing...")
        video_jobs[unique_id]["status"] = "transcribing"
        subtitle_path, translated_audio = generate_subtitles_and_audio(
            audio_path, language, unique_id
        )

        print("🎬 Merging video...")
        video_jobs[unique_id]["status"] = "merging"

        final_output_path = merge_all(
            video_path,
            translated_audio,
            subtitle_path,
            unique_id
        )

        print("✅ Completed!")
        video_jobs[unique_id]["status"] = "completed"
        video_jobs[unique_id]["output"] = os.path.basename(final_output_path)

    except Exception as e:
        print("❌ ERROR:", e)
        video_jobs[unique_id]["status"] = "error"
        video_jobs[unique_id]["output"] = str(e)
        
@app.route("/video_status/<job_id>")
def video_status(job_id):

    job = video_jobs.get(job_id)

    if not job:
        return jsonify({
            "status": "invalid",
            "completed": False,
            "video_url": None
        })

    if job["status"] == "completed":
        return jsonify({
            "status": "completed",
            "completed": True,
            "video_url": url_for(
                "uploaded_file",
                filename=job["output"]
            )
        })

    if job["status"] == "error":
        return jsonify({
            "status": "error",
            "completed": False,
            "video_url": None,
            "message": job["output"]
        })

    return jsonify({
        "status": job["status"],
        "completed": False,
        "video_url": None
    })

@app.route("/video_translation", methods=["GET", "POST"])
def video_translation():
    if request.method == "POST":
        video = request.files["video"]
        language = request.form["language"]
        unique_id = str(uuid.uuid4())

        try:
            video_path = os.path.join(app.config["UPLOAD_FOLDER"], f"input_video_{unique_id}.mp4")
            video.save(video_path)
            audio_path = extract_audio(video_path, unique_id)
            print("🚀 Calling subtitle function...")
            subtitle_path, translated_audio = generate_subtitles_and_audio(audio_path, language, unique_id)
            print("🚀 Subtitle function finished")
            final_video = merge_all(video_path, translated_audio, subtitle_path, unique_id)
            return render_template("video_output.html", translated_video=os.path.basename(final_video))
        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("video_translation.html")

# -------------------- LIVE MEETING SYSTEM --------------------

@app.route("/live-meeting")
def live_meeting():
    return render_template("live_meeting.html")

@app.route("/live_translate", methods=["POST"])
def live_translate():

    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target_lang", "en")

    if not text.strip():
        return jsonify({"translated": ""})

    try:
        # Reuse translator object (avoid recreating every time)
        if target_lang not in translator_cache:
            translator_cache[target_lang] = GoogleTranslator(
                source="auto",
                target=target_lang
            )

        translated = translator_cache[target_lang].translate(text)

    except Exception as e:
        print("Translation Error:", e)
        translated = text

    return jsonify({"translated": translated})

from gtts import gTTS

@app.route("/generate_voice", methods=["POST"])
def generate_voice():

    data = request.get_json()
    text = data.get("text", "")
    lang = data.get("lang", "en")

    filename = f"voice_{uuid.uuid4()}.mp3"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)

    return jsonify({"audio_url": f"/uploads/{filename}"})
    
# ----------------- TEXT TRANSLATION -------------------

import pyttsx3

import argostranslate.package
import argostranslate.translate


# ----------------- OFFLINE TRANSLATE -----------------

def offline_translate(text, target_lang):

    installed_languages = argostranslate.translate.get_installed_languages()

    # Find target language
    to_lang = None

    for lang in installed_languages:
        if lang.code == target_lang:
            to_lang = lang
            break

    if not to_lang:
        return None

    # Try all installed languages as source
    for lang in installed_languages:

        try:

            translation = lang.get_translation(to_lang)

            if translation:
                return translation.translate(text)

        except Exception:
            continue

    return None

# ----------------- HYBRID TRANSLATE -----------------

def hybrid_translate(text, target_lang):
    if not text or not text.strip():
        return "Please enter some text."

    supported_languages = {
        "ta": "ta",
        "en": "en",
        "te": "te",
        "kn": "kn"
    }

    target = supported_languages.get(target_lang)

    if not target:
        return "Unsupported target language."

    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text.strip(),
                "langpair": f"hi|{target}"
            },
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") == 200:
            result = data.get("responseData", {}).get(
                "translatedText", ""
            ).strip()

            if result:
                return result

        print("MyMemory API response:", data)
        return "Translation failed. Please try again."

    except Exception as e:
        print("MyMemory Translation Error:", repr(e))
        return "Translation failed. Please try again."

# ----------------- SENTENCE GENERATOR -----------------

def smart_example(word):

    if not word:
        return "No example available"

    patterns = [

        f"I said {word} to my friend.",

        f"She used the word {word} in a sentence.",

        f"They greeted me with {word}.",

        f"He didn't understand the meaning of {word}.",

        f"I often hear people say {word}."

    ]

    import random

    return random.choice(patterns)


# ----------------- MULTILINGUAL EXAMPLE -----------------

def smart_multilingual_example(word, target_lang):

    if not word:
        return "No example available"

    sentence = f"I said {word} to my friend."

    try:

        translated_sentence = GoogleTranslator(
            source="en-GB",
            target=target_lang
        ).translate(sentence)

        return translated_sentence

    except Exception:

        return sentence


# ----------------- GENERATE EXAMPLE -----------------

def generate_example(word, lang):

    if not word:
        return "No example available"

    import random

    patterns = [

        f"I said {word} to my friend.",

        f"She used {word} in a conversation.",

        f"They greeted me with {word}.",

        f"I hear {word} often in daily life."

    ]

    base_sentence = random.choice(patterns)

    try:

        translated = GoogleTranslator(
            source="en-GB",
            target=lang
        ).translate(base_sentence)

        return translated

    except Exception:

        return base_sentence


# ----------------- MEANING -----------------

def get_meaning(word):

    if not word:
        return "No meaning available."

    return f"'{word}' is a translated word used in daily conversation."


# ----------------- SUPPORTED LANGUAGES -----------------

SUPPORTED_TRANSLATION_LANGUAGES = {

    "Tamil": "ta",

    "Hindi": "hi",

    "Telugu": "te",

    "Kannada": "kn",

    "English": "en",

    "Malayalam": "ml"

}


# ----------------- TEXT TRANSLATION ROUTE -----------------

@app.route('/text-translation', methods=['GET', 'POST'])
def text_translation():

    translated_text = ""

    example_sentence = ""

    input_text = ""

    if request.method == "POST":

        input_text = request.form.get(
            "input_text",
            ""
        ).strip()

        output_lang = request.form.get(
            "output_lang",
            "en"
        )

        # Check whether selected language is supported
        if output_lang not in SUPPORTED_TRANSLATION_LANGUAGES.values():

            return render_template(
                "text_translation.html",
                translated_text="Unsupported target language.",
                example_sentence="",
                input_text=input_text
            )

        # Translate
        translated_text = hybrid_translate(
            input_text,
            output_lang
        )

        # Generate example without translating
        # the translated result back to English.
        example_sentence = smart_example(
            input_text
        )

    return render_template(
        "text_translation.html",
        translated_text=translated_text,
        example_sentence=example_sentence,
        input_text=input_text
    )


# ----------------- SIMPLE EXAMPLE -----------------

def simple_example(word):

    return f"This is an example using '{word}'."


# ----------------- VOICE ROUTE -----------------
# Online gTTS
# Offline pyttsx3 fallback

@app.route("/speak", methods=["POST"])
def speak():

    data = request.get_json()

    text = data.get("text")
    lang = data.get("lang")

    if not text:

        return jsonify({
            "error": "No text"
        }), 400

    try:

        if not os.path.exists("static"):

            os.makedirs("static")

        file_path = "static/output.mp3"

        try:

            # Online voice
            tts = gTTS(
                text=text,
                lang=lang
            )

            tts.save(file_path)

        except Exception:

            # Offline voice
            engine = pyttsx3.init()

            engine.save_to_file(
                text,
                file_path
            )

            engine.runAndWait()

        return jsonify({
            "audio_url": "/static/output.mp3"
        })

    except Exception:

        return jsonify({
            "error": "Voice failed"
        }), 500

# import os

# # 🔥 FIX HERE FIRST
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# from huggingface_hub.utils import logging
# logging.set_verbosity_error()

# # THEN import
# from faster_whisper import WhisperModel

# ---------- HOME ----------
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("home.html", username=session["username"])

# ---------- EDIT PROFILE ----------
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    user = db.execute(
        "SELECT username, email, purpose FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        purpose = request.form["purpose"]

        db.execute("""
            UPDATE users
            SET username=?, email=?, purpose=?
            WHERE id=?
        """, (
            username,
            email,
            purpose,
            session["user_id"]
        ))

        db.commit()

        session["username"] = username

        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=user)

# ---------- CHANGE PASSWORD ----------
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        db = get_db()

        user = db.execute(
            "SELECT password FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if not user:
            return redirect(url_for("login"))

        # Verify current password
        if not check_password_hash(user["password"], current_password):
            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        # Check new password and confirm password
        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        # Prevent using the same password
        if current_password == new_password:
            return render_template(
                "change_password.html",
                error="New password must be different from current password."
            )

        # Validate password strength
        if not strong_password(new_password):
            return render_template(
                "change_password.html",
                error="Password must contain at least 8 characters, one uppercase letter, one lowercase letter, and one number."
            )

        # Save hashed password
        hashed_password = generate_password_hash(new_password)

        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (hashed_password, session["user_id"])
        )

        db.commit()

        return redirect(url_for("profile"))

    return render_template("change_password.html")

# ---------- ADMIN PASSWORD ----------
@app.route("/admin-password", methods=["GET", "POST"])
def admin_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    user = db.execute(
        "SELECT is_admin FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    if not user or not user["is_admin"]:
        return redirect(url_for("admin", denied=1))

    if request.method == "POST":

        admin_password = request.form["admin_password"]

        # Temporary admin password
        if admin_password != "Admin@123":
            return render_template(
                "admin_password.html",
                error="Incorrect admin password."
            )

        session["is_admin"] = True

        return redirect(url_for("admin_dashboard"))

    return render_template("admin_password.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin-dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only verified admin can access
    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    db = get_db()

    search = request.args.get("search", "").strip()

    if search:
        keyword = f"%{search}%"

        users = db.execute("""
            SELECT id, username, email, purpose, is_verified, is_admin
            FROM users
            WHERE is_deleted=0
                AND (
                    username LIKE ?
                    OR email LIKE ?
                    OR purpose LIKE ?
                )
            ORDER BY id DESC
        """, (keyword, keyword, keyword)).fetchall()

    else:   
        users = db.execute("""
            SELECT id, username, email, purpose, is_verified, is_admin 
            FROM users
            WHERE is_deleted=0
            ORDER BY id DESC
    """).fetchall()

    return render_template(
        "admin_dashboard.html",
        users=users,
        search=search
    )

# ---------- ADMIN USER DETAILS ----------

@app.route("/admin-user/<int:user_id>")
def admin_user_details(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    db = get_db()

    user = db.execute("""
        SELECT id, username, email, purpose, is_verified, is_admin
        FROM users
        WHERE id=? AND is_deleted=0
    """, (user_id,)).fetchone()

    if not user:
        return redirect(url_for("admin_dashboa"))

    return render_template(
        "admin_user_details.html",
        user=user
    )

# ---------- DELETED ACCOUNTS ----------
@app.route("/deleted-accounts")
def deleted_accounts():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    db = get_db()

    deleted_users = db.execute("""
        SELECT id, username, email, purpose, is_verified
        FROM users
        WHERE is_deleted=1
        ORDER BY id DESC
    """).fetchall()

    return render_template(
        "deleted_accounts.html",
        users=deleted_users
    )

# ----------- Restore deleted user ---------------
@app.route("/restore-user/<int:user_id>", methods=["POST"])
def restore_user(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    db = get_db()

    db.execute(
        """
        UPDATE users
        SET is_deleted=0
        WHERE id=? AND is_deleted=1
        """,
        (user_id,)
    )

    db.commit()

    return redirect(url_for("deleted_accounts"))

# ----------- Delete user ---------------
@app.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    db = get_db()

    # Prevent deleting an admin account
    target_user = db.execute(
        "SELECT is_admin FROM users WHERE id=? AND is_deleted=0",
        (user_id,)
    ).fetchone()

    if target_user and target_user["is_admin"] == 1:
        return redirect(url_for("admin_dashboard"))

    db.execute(
        "UPDATE users SET is_deleted=1 WHERE id=?",
        (user_id,)
    )

    db.commit()

    return redirect(url_for("admin_dashboard"))

# ---------- ADMIN ACCESS ----------
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))

    error = None

    if request.args.get("denied") == "1":
        error = "You are not allowed to access this page. This page is only for administrators."

    return render_template(
        "admin.html",
        error=error
    )
# ---------- PROFILE ----------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    user = db.execute(
        "SELECT username, email, purpose FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)