# AI Translator 🌐

An AI-powered multilingual translation application designed to translate
different types of content such as **text, images, uploaded videos,
YouTube videos, and live audio/meetings** into the user's preferred language.

The project combines artificial intelligence, speech recognition, machine
translation, text-to-speech, OCR, and multimedia processing technologies
to build an end-to-end translation platform.

> **Project Status:** 🚧 Currently under development and testing.
>
> The major features have been implemented progressively, but the project
> has not yet reached a completely stable working condition. Individual
> modules are currently being tested, debugged, and improved before the
> final release.

---

## ✨ Features

### 📝 Text Translation

- Translate user-provided text into a selected target language.
- Supports multilingual input and output processing.
- Translation output is currently being tested for accuracy and reliability.
- Different translation backends are being evaluated during development.

> **Current Status:** 🚧 Testing and debugging

---

### 📖 Dictionary

The dictionary module is designed to provide:

- Word translation
- Word meaning
- Example sentences
- Pronunciation support
- Audio generation
- Copy functionality

> **Current Status:** 🚧 Feature implemented and under testing

---

### 🖼️ Image Translation

The image translation module is designed to:

- Accept an image as input
- Extract text from the image using OCR
- Process the extracted text
- Translate the detected text into the selected language

> **Current Status:** 🚧 Testing

---

### 🎥 Video Translation

The video translation module is designed to:

- Accept an uploaded video
- Extract audio from the video
- Convert speech into text
- Translate the extracted speech
- Generate translated audio
- Process the translated output

The project uses speech recognition and multimedia processing tools to
build the video translation pipeline.

> **Current Status:** 🚧 Testing and debugging

---

### ▶️ YouTube Translation

The YouTube translation module is designed to:

- Accept a YouTube video URL
- Process the video's audio
- Convert speech into text
- Translate the extracted content
- Generate translated audio/subtitle output

The YouTube translation pipeline is being developed as part of the
overall multimedia translation system.

> **Current Status:** 🚧 Testing

---

### 🎙️ Speech-to-Text

The application uses AI-based speech recognition to convert spoken audio
into text.

The project uses:

- Whisper
- Faster-Whisper

for speech recognition and transcription tasks.

> **Current Status:** 🚧 Implemented and under testing

---

### 🔊 Text-to-Speech

The application can generate speech audio from translated text.

Technologies used include:

- Google Text-to-Speech (gTTS)
- pyttsx3

> **Current Status:** 🚧 Implemented and under testing

---

### 🗣️ Live Translation

The project includes functionality for processing live speech and
translating it into the selected language.

The long-term goal is to support translation during:

- Live meetings
- Online classes
- Voice communication
- Other real-time speech scenarios

> **Current Status:** 🚧 Development and testing

---

## 👤 User Account System

The application includes a user authentication and account management
system.

Implemented functionality includes:

- User registration
- Login
- Logout
- OTP verification
- Forgot password
- Password reset
- User profile
- User details
- Session management

The home page also provides a profile interface for logged-in users.

> **Current Status:** ✅ Implemented and tested

---

## 🛡️ Admin System

An admin account management system has also been implemented.

The admin functionality includes:

- Admin account recognition during login
- Admin-only access
- Admin password verification
- Admin dashboard
- Registered user listing
- User search
- Individual user details
- User deletion
- Deleted user management
- User restoration

### 🔐 Admin Protection

The admin account is protected from accidental deletion.

Normal users can be deleted and restored by an authorized administrator,
while the admin account remains protected.

> **Current Status:** ✅ Implemented and tested

---

## 🗑️ Deleted Account Management

The application uses a soft-delete approach for user accounts.

Instead of permanently removing a user from the database:

- The account is marked as deleted.
- Deleted accounts are displayed separately.
- An administrator can restore a deleted account.
- Restored accounts can appear again in the active users list.

This allows account management without permanently removing database records.

> **Current Status:** ✅ Implemented and tested

---

## 🛠️ Technologies Used

### Programming & Web

- **Python**
- **Flask**
- **HTML**
- **CSS**
- **JavaScript**

### AI & Speech Processing

- **Whisper**
- **Faster-Whisper**
- **OpenAI API**
- **Speech Processing Libraries**

### Translation

- **Machine Translation APIs/Libraries**
- **Deep Translator**
- **Argos Translate**

### Audio & Video Processing

- **FFmpeg**
- **OpenCV**
- **gTTS**
- **pyttsx3**
- **sounddevice**
- **librosa**

### Image Processing

- **PyTesseract**
- **Pillow**
- **OpenCV**

### YouTube Processing

- **yt-dlp**

### Database

- **SQLite**

---

## 🔄 Overall Translation Workflow

The application follows a modular translation pipeline:

**Input → Text/Speech Extraction → Translation → Audio Generation → Output**

Depending on the input type, the workflow changes.

### Text

**Text Input → Translation → Translated Text → Optional Audio**

### Image

**Image → OCR → Extracted Text → Translation → Output**

### Video

**Video → Audio Extraction → Speech-to-Text → Translation → Text-to-Speech → Output Video/Audio**

### YouTube

**YouTube URL → Audio/Video Processing → Speech-to-Text → Translation → Audio/Subtitle Output**

### Live Speech

**Live Audio → Speech Recognition → Translation → Translated Output**

---

## 🧪 Current Development & Testing Status

The project is currently in the **development and testing phase**.

The main application structure and several major modules have already
been implemented. However, the complete application is **not yet in
final stable working condition**.

Current testing focuses on:

- Text translation reliability
- Multilingual translation output
- Translation backend stability
- Image OCR and translation
- Video processing
- YouTube processing
- Speech recognition
- Text-to-speech generation
- Live translation
- User authentication
- Admin functionality
- Account deletion and restoration
- Integration between different modules

Some modules may work individually while others are still being debugged
or improved.

The project will be considered complete only after the major modules are
tested together and the complete application works reliably.

---

## 🚧 Current Known Development Area

The **text translation module** is currently being tested with multiple
Indian languages.

The project is evaluating translation backends because the currently
used translation services may have request limitations or incomplete
language support.

The target is to provide reliable translation for languages such as:

- 🇮🇳 Tamil
- 🇮🇳 Hindi
- 🇮🇳 Telugu
- 🇮🇳 Kannada
- 🇮🇳 Malayalam
- 🇬🇧 English

This module is still under development and should not yet be considered
final or fully stable.

---

## 🎯 Project Goal

The main goal of this project is to develop a **single AI-based
multimedia translation platform** capable of handling different forms
of content through one web application.

The project aims to combine:

- Artificial Intelligence
- Machine Translation
- Speech Recognition
- Text-to-Speech
- Optical Character Recognition
- Audio Processing
- Video Processing
- User Authentication
- Database Management

into one practical translation platform.

---

## 🔮 Future Improvements

Planned improvements include:

- More reliable multilingual translation
- More Indian and international language support
- Improved translation accuracy
- Translation history
- Better translation backend
- Speaker identification
- Better voice synchronization
- Faster video processing
- Improved real-time translation
- Google Meet translation
- Zoom translation
- Cloud deployment
- Scalable processing
- Improved user interface
- Better error handling
- Complete end-to-end testing

---

## 📌 Development Approach

The project is being developed incrementally.

Each major functionality is implemented, tested, debugged, and integrated
before moving to the next stage.

The current development process focuses on:

**Build → Test → Identify Issues → Fix → Retest → Integrate**

The application is therefore an ongoing project rather than a final
released product.

---

## 👩‍💻 Author

**Yuvashree**

---

⭐ If you find this project interesting, feel free to explore the
repository and follow its development.

---