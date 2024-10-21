import streamlit as st
import os
import requests
from moviepy.editor import VideoFileClip, AudioFileClip

AZURE_TTS_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/tts/audio/speech?api-version=2024-05-01-preview"
AZURE_API_KEY = "3b7e7e5627b2414a8755a7a42b7f5922"


OPENAI_API_KEY = "22ec84421ec24230a3638d1b51e3a7dc"
OPENAI_ENDPOINT = "https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"

AZURE_WHISPER_ENDPOINT = "https://curio-m22u9hu0-swedencentral.openai.azure.com/openai/deployments/whisper/audio/translations?api-version=2024-06-01"

def transcribe_audio_with_timestamps(audio_file):
    headers = {
        "api-key": AZURE_API_KEY,
    }

    with open(audio_file, "rb") as audio:
        files = {
            'file': (audio_file, audio, 'audio/wav') 
        }
        response = requests.post(AZURE_WHISPER_ENDPOINT, headers=headers, files=files)

   
    if response.status_code != 200:
        st.error("Error in transcription: " + response.text)
        return None

    response_data = response.json()

   
    if 'text' in response_data:
        return response_data['text']
    else:
        st.error("Error: Transcription text not found in response.")
        return None


def process_timestamps(transcriptions):
    speaking_segments = []
    
   
    if 'segments' in transcriptions:
        for segment in transcriptions['segments']:
            start = segment['start']
            end = segment['end']
            speaking_segments.append((start, end))
    else:
        st.error("No 'segments' found in the transcriptions.")
    
    return speaking_segments

def correct_transcription(transcription):
    headers = {
        "Content-Type": "application/json",
        "api-key": OPENAI_API_KEY,
    }
    data = {
        "messages": [{"role": "system", "content": f"Correct this transcription: {transcription}"}],
    }

    response = requests.post(OPENAI_ENDPOINT, headers=headers, json=data)

   
    if response.status_code != 200:
        st.error(f"Error in GPT-4 API request: {response.status_code} - {response.text}")
        return None

    try:
       
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        st.error(f"Unexpected response format: {response.json()}")
        return None

def generate_audio(text):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY, 
    }
    data = {
        "model": "tts-1-hd",
        "input": text,
        "voice": "alloy",
    }

    response = requests.post(AZURE_TTS_ENDPOINT, headers=headers, json=data)

    if response.status_code == 200:
        with open("new_audio.mp3", "wb") as out:
            out.write(response.content)
    else:
        st.error("Error generating audio: " + response.text)

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
        
        
        video_clip = VideoFileClip("uploaded_video.mp4")
        video_clip.audio.write_audiofile("uploaded_audio.wav", codec='pcm_s16le')

        
        if not os.path.exists("uploaded_audio.wav"):
            st.error("Audio extraction failed. Please check the uploaded video file.")
            return
        
       
        transcriptions = transcribe_audio_with_timestamps("uploaded_audio.wav")
        
       
        if transcriptions is None:
            st.error("Transcription failed. Please check the audio file.")
            return

        
        full_transcription = transcriptions  

       
        corrected_transcription = correct_transcription(full_transcription)

       
        generate_audio(corrected_transcription)

       
        replace_video_audio("uploaded_video.mp4", "new_audio.mp3")

        st.success("Download your video below.")
        st.video("output_video.mp4")

if __name__ == "__main__":
    main()
