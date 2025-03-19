import streamlit as st
import os
import zipfile
from pydub import AudioSegment
from io import BytesIO


# Streamlit UI
st.title("Split audio chunks")

# File uploaders
mp3_file = st.file_uploader("Upload mp3 File", type=["mp3"])
if mp3_file:
    try:
        #🔹 Python Code to Split by 23MB Chunks
        # Load the MP3 file
        audio = AudioSegment.from_file(mp3_file, format="mp3")

        # Set the desired file size (25MB)
        target_size_mb = 23
        target_size_bytes = target_size_mb * 1024 * 1024  # Convert to bytes

        # Get bitrate (in bits per second)
        bitrate_kbps = 128  # Change this based on your file (128 kbps is common)
        bitrate_bps = bitrate_kbps * 1000  # Convert to bps

        # Calculate how many milliseconds fit into 25MB
        max_duration_ms = (target_size_bytes * 8) / bitrate_bps * 1000  # Convert to ms

        # Split audio into chunks
        start = 0
        part = 1
        chunk_files = []

        while start < len(audio):
            end = min(start + max_duration_ms, len(audio))
            chunk = audio[start:end]
            
            # Save chunk to a BytesIO buffer
            chunk_buffer = BytesIO()
            chunk.export(chunk_buffer, format="mp3", bitrate=f"{bitrate_kbps}k")
            chunk_buffer.seek(0)

            chunk_files.append((f"SMED_Meeting_Part{part}.mp3", chunk_buffer.read()))
            start = end
            part += 1


        # Create a ZIP file for downloading
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename, filedata in chunk_files:
                zipf.writestr(filename, filedata)
        zip_buffer.seek(0)

        st.success("Processing complete! Click below to download the MP3 chunks.")

        # Provide download button for the ZIP file
        st.download_button(label="Download MP3 Files",
                           data=zip_buffer,
                           file_name="split_audio_files.zip",
                           mime="application/zip")
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
