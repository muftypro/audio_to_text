# app.py

import os
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
from datetime import datetime

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/audio"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def convert_audio_to_text(audio_path):
    # Convert MP3 to WAV for compatibility
    audio = AudioSegment.from_mp3(audio_path)
    wav_path = audio_path.replace(".mp3", ".wav")
    audio.export(wav_path, format="wav")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    chunk_length_ms = 60000  # 1 minute chunks
    audio_chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    transcription = []

    # Process each chunk
    for i, chunk in enumerate(audio_chunks, 1):
        chunk_path = f"{i}.wav"
        chunk.export(chunk_path, format="wav")
        with sr.AudioFile(chunk_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="bn-BD")  # Bengali/English
                transcription.append(text)
            except sr.UnknownValueError:
                transcription.append("[Unrecognized speech]")
            except sr.RequestError:
                transcription.append("[API error or network issue]")
        
        os.remove(chunk_path)  # Clean up chunk files

    return "\n".join(transcription)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        if not file.filename.endswith(".mp3"):
            return jsonify({"error": "Only MP3 files are supported"}), 400
        
        # Save uploaded file
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], datetime.now().strftime("%Y%m%d%H%M%S") + "_" + file.filename)
        file.save(file_path)

        # Convert and transcribe
        transcription = convert_audio_to_text(file_path)
        
        # Cleanup uploaded file after transcription
        os.remove(file_path)
        
        return jsonify({"transcription": transcription})
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
