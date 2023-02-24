from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import moviepy.editor as mp
import numpy as np
import time
from google.cloud import translate_v2 as translate
import urllib.request
import deepspeech

app = Flask(__name__)

# Initialize Google Translate API client
translate_client = translate.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_files():
    # Get user-uploaded video file and language preference from HTML form
    video_file = request.files['video']
    source_language = request.form['source_language']
    target_language = request.form['target_language']

    # Download the necessary model files
    if source_language == "en":
        model_url = "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"
        scorer_url = "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer"
    elif source_language == "fr":
        model_url = "https://github.com/Common-Voice/commonvoice-fr/releases/download/v1/fr-deepspeech-0.9.3-models.pbmm"
        scorer_url = "https://github.com/Common-Voice/commonvoice-fr/releases/download/v1/fr-deepspeech-0.9.3-models.scorer"
    elif source_language == "es":
        model_url = "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"
        scorer_url = "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer"
    else:
        return "Unsupported source language"

    # Download the model files
    model_file = urllib.request.urlopen(model_url).read()
    scorer_file = urllib.request.urlopen(scorer_url).read()

    # Initialize the DeepSpeech model
    ds = deepspeech.Model.from_buffer(model_file)

    # Set the model's scorer
    ds.enableExternalScorer(scorer_file)

    # Save user-uploaded video file
    video_file_path = os.path.join('static', 'uploads', video_file.filename)
    video_file.save(video_file_path)

    # Use MoviePy to convert video to audio
    audio_file_path = os.path.join('static', 'uploads', os.path.splitext(video_file.filename)[0] + '.wav')
    video = mp.VideoFileClip(video_file_path)
    video.audio.write_audiofile(audio_file_path)

    # Use DeepSpeech to transcribe audio
    audio = np.fromfile(audio_file_path, dtype=np.int16)
    transcript = ds.stt(audio)

    # Use Google Translate API to translate transcript to target language
    translation = translate_client.translate(transcript, target_language=target_language, source_language=source_language)

    # Create output file with translated captions
    output_file_path = os.path.join('static', 'uploads', os.path.splitext(video_file.filename)[0] + '_' + target_language + '.srt')
    with open(output_file_path, 'w') as f:
        f.write('1\n')
        f.write('00:00:00,000 --> 00:00:05,000\n')
        f.write(translation['translatedText'] + '\n')

    # Use MoviePy to add captions to video
    output_video_file_path = os.path.join('static', 'uploads', os.path.splitext(video_file.filename)[0] + '_' + target_language + '.mp4')
    video = mp.VideoFileClip(video_file_path)
    video = video.subclip(0, video.duration - 1)
    captions = mp.TextClip(translation['translatedText'], fontsize=40, color='white', font='Arial', bg_color='black', stroke_width=0.5).set_position
