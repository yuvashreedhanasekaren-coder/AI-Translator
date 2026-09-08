import os
import subprocess

uploads_dir = r"C:\Users\ADMIN\OneDrive\Desktop\AI_Translator\uploads"

input_video = os.path.join(uploads_dir, "input_video_12af55f8-19c6-4728-ab34-d7a57a5daeba.mp4")
translated_audio = os.path.join(uploads_dir, "translated_audio_12af55f8-19c6-4728-ab34-d7a57a5daeba.mp3")
subtitles_file = os.path.join(uploads_dir, "subtitles_12af55f8-19c6-4728-ab34-d7a57a5daeba.srt")
output_file = os.path.join(uploads_dir, "final_output.mp4")

# FFmpeg likes forward slashes
subtitles_ffmpeg = subtitles_file.replace("\\", "/")

# Use single quotes around the style part
vf_filter = f"subtitles={subtitles_ffmpeg}"

ffmpeg_command = [
    "ffmpeg",
    "-y",
    "-i", input_video,
    "-i", translated_audio,
    "-vf", vf_filter,
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-c:a", "aac",
    "-shortest",
    output_file
]

try:
    subprocess.run(ffmpeg_command, check=True)
    print("✅ Video merged successfully! Output at:", output_file)
except subprocess.CalledProcessError as e:
    print("❌ FFmpeg error:", e)
    