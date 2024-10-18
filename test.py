import streamlit as st
import os
import requests
from moviepy.editor import VideoFileClip, AudioFileClip

# Azure API settings
AZURE_TTS_KEY = "3b7e7e5627b2414a8755a7a42b7f5922"
AZURE_TTS_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/tts/audio/speech?api-version=2024-05-01-preview"

AZURE_WHISPER_KEY = "3b7e7e5627b2414a8755a7a42b7f5922"
AZURE_WHISPER_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/whisper/audio/translations?api-version=2024-06-01"

def transcribe_audio_with_whisper(audio_file):
    with open(audio_file, 'rb') as f:
        audio_data = f.read()

    headers = {
        "Content-Type": "audio/wav",
        "Authorization": f"Bearer {AZURE_WHISPER_KEY}",
    }

    response = requests.post(AZURE_WHISPER_ENDPOINT, headers=headers, data=audio_data)

    if response.status_code == 200:
        return response.json()["text"]
    else:
        st.error(f"Error in Whisper API: {response.text}")
        return ""

def generate_audio_with_tts(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AZURE_TTS_KEY}",
    }
    
    data = {
        "input": {"text": text},
        "voice": {"language_code": "en-US", "name": "en-US-JennyNeural"},
        "audioConfig": {"audioEncoding": "MP3"}
    }

    response = requests.post(AZURE_TTS_ENDPOINT, headers=headers, json=data)
    
    if response.status_code == 200:
        with open("new_audio.mp3", "wb") as audio_file:
            audio_file.write(response.content)
        st.success("Audio generated successfully!")
    else:
        st.error(f"Error in TTS API: {response.text}")

def replace_video_audio(video_file, final_audio_file):
    video = VideoFileClip(video_file)
    new_audio = AudioFileClip(final_audio_file)
    video = video.set_audio(new_audio)
    video.write_videofile("output_video.mp4", codec='libx264')

def main():
    st.title("Azure TTS and STT with Video Processing")

    video_file = st.file_uploader("Upload a video", type=["mp4", "mov"])
    
    if video_file:
        # Save the uploaded video to a file
        with open("uploaded_video.mp4", "wb") as f:
            f.write(video_file.read())
        
        # Extract audio from the video
        video = VideoFileClip("uploaded_video.mp4")
        video.audio.write_audiofile("uploaded_audio.wav")
        
        # Transcribe audio using Whisper
        st.info("Transcribing audio with Whisper...")
        transcription = transcribe_audio_with_whisper("uploaded_audio.wav")
        
        if transcription:
            st.text_area("Transcription", transcription)
            
            # Generate audio using Azure TTS
            st.info("Generating audio with Azure TTS...")
            generate_audio_with_tts(transcription)
            
            # Replace the audio in the video with the new TTS audio
            st.info("Replacing video audio...")
            replace_video_audio("uploaded_video.mp4", "new_audio.mp3")
            
            st.success("Processing completed!")
            st.video("output_video.mp4")

if __name__ == "__main__":
    main()