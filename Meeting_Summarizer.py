import sys
import os
import json
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout
from pydub import AudioSegment
import whisper
from openai import OpenAI
from moviepy import VideoFileClip

# Set your OpenAI API key here
client = OpenAI(api_key="", base_url="https://api.deepseek.com")

class AudioTranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Audio Transcription & Summary")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select an audio/video file:")
        layout.addWidget(self.label)

        self.btn_select = QPushButton("Choose File")
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)

        self.btn_process = QPushButton("Process File")
        self.btn_process.clicked.connect(self.process_file)
        layout.addWidget(self.btn_process)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Audio/Video Files (*.mp3 *.mp4 *.wav *.m4a *.avi)")
        if file_path:
            self.file_path = file_path
            self.label.setText(f"Selected: {os.path.basename(file_path)}")

    def process_file(self):
        if not hasattr(self, 'file_path'):
            self.label.setText("No file selected!")
            return

        file_path = self.file_path

        # Convert video to audio if needed
        if file_path.endswith(('.mp4', '.avi', '.m4a')):
            self.label.setText("Converting video to audio...")
            audio = VideoFileClip(file_path).audio
            audio_path = file_path.replace(".mp4", ".mp3").replace(".avi", ".mp3").replace(".m4a", ".mp3")
            audio.write_audiofile(audio_path)
        else:
            audio_path = file_path

        # Convert audio to MP3
        if not audio_path.endswith('.mp3'):
            self.label.setText("Converting audio to MP3...")
            audio = AudioSegment.from_file(audio_path)
            audio.export("output.mp3", format="mp3")
            audio_path = "output.mp3"

        # Split Audio by 23MB Chunks
        audio = AudioSegment.from_mp3(audio_path)

        # Calculate how many milliseconds fit into 25MB
        max_duration_ms = (23 * 1024 * 1024 * 8) / 23 * 1024 * 1024 * 1000 * 1000  # Convert to ms

        # Split audio into chunks
        audio_chunks = []  # List to store chunk file paths
        start = 0
        part = 1
        while start < len(audio):
            end = min(start + max_duration_ms, len(audio))
            chunk = audio[start:end]
            
            # Export each chunk
            output_file = os.path.join("..", f"{part}.mp3")
            chunk.export(output_file, format="mp3", bitrate="128 k")
            print(f"Saved: {output_file}")

            audio_chunks.append(output_file)  # Store chunk file path
            start = end
            part += 1
            audio_chunks  # Return list of audio chunks


        
        # Transcribe using Whisper
        self.label.setText("Transcribing audio...")
        model = whisper.load_model("base", device="cpu")
        transcripts = {}

        for chunk_path in audio_chunks:
            print(f"Transcribing: {chunk_path}")
            result = model.transcribe(chunk_path)
            transcripts[chunk_path] = result["text"]  # Store transcribed text

        # Save all transcripts as JSON
        transcript_json = "transcript.json"
        with open(transcript_json, "w", encoding="utf-8") as json_file:
            json.dump(transcripts, json_file, ensure_ascii=False, indent=4)

        print(f"Transcript saved to {transcript_json}")


        # Define prompts
        prompts_dict = {
            "summary": """
                **Summary**: Provide a clear summary of the meeting, focusing on the main points discussed. The summary should capture the overall purpose and major discussions.
            """,
            "action_items": """
                **Action Items**: Identify clear, actionable statements.
            """,
            "key_questions": """
                **Key Questions**: Identify important questions raised during the meeting, including:
            """,
        }

        # Additional instructions
        additional_instructions = """
        **Additional Requirements**:
        - Donot generate any content outside of the defined markdown structure.
        - Ensure accuracy in speaker identification and timestamps. The timestamps must accurately match the content and speaker's statements.
        - The response should **not** include irrelevant details, opinions, or hallucinations.
        """

        # Construct the final prompt
        final_prompt = f"""
        Analyze the content of the provided audio file and identify the following elements in a **markdown** format:
        {prompts_dict['summary']}
        {prompts_dict['action_items']}
        {prompts_dict['key_questions']}
        {additional_instructions}
        """

        # Generate summary & action items using OpenAI GPT

        self.label.setText("Generating summary & action items...")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an AI assistant that extracts structured meeting insights."},
                {"role": "user", "content": final_prompt},
                {"role": "user", "content": transcript_json}
            ],
            temperature=0.3,
        )

        summary = response.choices[0].message.content

        # Save summary & action items
        output_file = "meeting_summary.md"
        with open(output_file, "w", encoding="utf-8") as md_file:
            md_file.write(summary)

        self.label.setText(f"Processing complete! Summary saved to {output_file}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AudioTranscriptionApp()
    ex.show()
    sys.exit(app.exec())
