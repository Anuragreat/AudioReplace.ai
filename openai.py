import streamlit as st
import os
import requests
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"  # google vertex AI credentials 


OPENAI_API_KEY = "22ec84421ec24230a3638d1b51e3a7dc"
OPENAI_ENDPOINT = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"


def transcribe_audio_with_timestamps(audio_file):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=audio_file)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    response = client.recognize(config=config, audio=audio)
    transcriptions = []
    for result in response.results:
        for word_info in result.alternatives[0].words:
            transcriptions.append((word_info.word, word_info.start_time, word_info.end_time))
    return transcriptions

def process_timestamps(transcriptions):
    speaking_segments = []
    for _, start, end in transcriptions:
        speaking_segments.append((start.total_seconds(), end.total_seconds()))
    return speaking_segments

def correct_transcription(transcription):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {
        "messages": [{"role": "user", "content": f"Correct this transcription: {transcription}"}],
        "temperature": 0.5,
    }
    response = requests.post(OPENAI_ENDPOINT, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]


def generate_audio(text):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name="en-US-Wavenet-D"  # Choose your preferred voice
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    with open("new_audio.mp3", "wb") as out:
        out.write(response.audio_content)


def replace_video_audio(video_file, final_audio_file):
    video = VideoFileClip(video_file)
    new_audio = AudioFileClip(final_audio_file)
    video = video.set_audio(new_audio)
    video.write_videofile("output_video.mp4", codec='libx264')





def main():
    st.title("Video Audio Fixing with AI Voice")
    
    video_file = st.file_uploader("Upload a video ", type=["mp4", "mov"])

    if video_file:
        with open("uploaded_video.mp4", "wb") as f:
            f.write(video_file.read())
        
        
        
        transcriptions = transcribe_audio_with_timestamps("uploaded_audio.wav")
        
        
        speaking_segments = process_timestamps(transcriptions)

        
        full_transcription = " ".join(word for word, _, _ in transcriptions)
        
        
        corrected_transcription = correct_transcription(full_transcription)

        
        generate_audio(corrected_transcription)

        
        replace_video_audio("uploaded_video.mp4", "new_audio.mp3")

        st.success("Download your video below.")
        st.video("output_video.mp4")

if __name__ == "__main__":
    main()
