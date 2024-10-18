import streamlit as st
import os
import requests
from moviepy.editor import VideoFileClip, AudioFileClip

# Set Azure credentials
AZURE_TTS_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/tts/audio/speech?api-version=2024-05-01-preview"
AZURE_API_KEY = "3b7e7e5627b2414a8755a7a42b7f5922"

# Set OpenAI credentials
OPENAI_API_KEY = "22ec84421ec24230a3638d1b51e3a7dc"
OPENAI_ENDPOINT = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

AZURE_WHISPER_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/whisper/audio/translations?api-version=2024-06-01"

def transcribe_audio_with_timestamps(audio_file):
    headers = {
        "Authorization": f"Bearer {AZURE_API_KEY}",  # Use this if it's a bearer token; otherwise use the API key directly
        "Content-Type": "application/octet-stream",
    }

    with open(audio_file, "rb") as audio:
        response = requests.post(AZURE_WHISPER_ENDPOINT, headers=headers, data=audio)

    # Check if the response is successful
    if response.status_code != 200:
        st.error("Error in transcription: " + response.text)
        return None

    return response.json()




def process_timestamps(transcriptions):
    speaking_segments = []
    for segment in transcriptions['segments']:
        start = segment['start']
        end = segment['end']
        speaking_segments.append((start, end))
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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AZURE_API_KEY}",
    }
    data = {
        "text": text,
        "voice": "en-US-JennyNeural",
        "audioFormat": "mp3"
    }

    response = requests.post(AZURE_TTS_ENDPOINT, headers=headers, json=data)

    with open("new_audio.mp3", "wb") as out:
        out.write(response.content)

def replace_video_audio(video_file, final_audio_file):
    video = VideoFileClip(video_file)
    new_audio = AudioFileClip(final_audio_file)
    video = video.set_audio(new_audio)
    video.write_videofile("output_video.mp4", codec='libx264')
    
def main():
    st.title("Video Audio Fixing with AI Voice")
    
    video_file = st.file_uploader("Upload a video ", type=["mp4", "mov"])

    if video_file:
        # Save the uploaded video file
        with open("uploaded_video.mp4", "wb") as f:
            f.write(video_file.read())
        
        # Extract audio from video
        video_clip = VideoFileClip("uploaded_video.mp4")
        video_clip.audio.write_audiofile("uploaded_audio.wav", codec='pcm_s16le')

        # Check if audio extraction was successful
        if not os.path.exists("uploaded_audio.wav"):
            st.error("Audio extraction failed. Please check the uploaded video file.")
            return
        
        # Now transcribe the extracted audio
        transcriptions = transcribe_audio_with_timestamps("uploaded_audio.wav")
        
        # Check if transcription was successful
        if transcriptions is None:
            st.error("Transcription failed. Please check the audio file.")
            return
        
        speaking_segments = process_timestamps(transcriptions)

        full_transcription = " ".join(segment['text'] for segment in transcriptions['segments'])
        
        corrected_transcription = correct_transcription(full_transcription)

        generate_audio(corrected_transcription)

        replace_video_audio("uploaded_video.mp4", "new_audio.mp3")

        st.success("Download your video below.")
        st.video("output_video.mp4")

if __name__ == "__main__":
    main()
