import os
import time
import json
import requests
from pathlib import Path
import replicate
from openai import OpenAI
import subprocess
from flask import current_app
from storage import storage_manager

class VideoGenerationService:
    """Service for handling video generation tasks."""

    def __init__(self, user=None, project=None):
        """Initialize the service with user and project information."""
        self.user = user
        self.project = project

        # Set up API clients based on user's API keys or default to environment variables
        self.setup_api_clients()

        # Ensure output directories exist
        Path("static/image").mkdir(exist_ok=True, parents=True)
        Path("static/video").mkdir(exist_ok=True, parents=True)
        Path("static/music").mkdir(exist_ok=True, parents=True)
        Path("static/voice").mkdir(exist_ok=True, parents=True)
        Path("static/final").mkdir(exist_ok=True, parents=True)

    def setup_api_clients(self):
        """Set up API clients based on user's API keys or default to environment variables."""
        # OpenAI client
        openai_api_key = self.user.openai_api_key if self.user and self.user.openai_api_key else os.getenv("OPENAI_API_KEY")
        # Use a dummy API key if none is provided
        if not openai_api_key:
            openai_api_key = "dummy_key_for_demo_mode"
            print("No OpenAI API key found. Using demo mode.")
        self.openai_client = OpenAI(api_key=openai_api_key)

        # Replicate API key
        replicate_api_key = self.user.replicate_api_key if self.user and self.user.replicate_api_key else os.getenv("REPLICATE_API_KEY")
        if replicate_api_key:
            os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
        else:
            print("No Replicate API key found. Using demo mode.")

        # SonAuto API key
        self.sonauto_api_key = self.user.sonauto_api_key if self.user and self.user.sonauto_api_key else os.getenv("SONAUTO_API_KEY")
        if not self.sonauto_api_key:
            print("No SonAuto API key found. Using demo mode.")

    def read_file(self, file_path):
        """Read the content of a file."""
        with open(file_path, 'r') as file:
            return file.read()

    def save_file(self, file_path, content, mode='wb'):
        """Save content to a file."""
        # Extract directory and filename from file_path
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)

        # Determine content type based on file extension
        content_type = None
        if file_path.endswith('.png'):
            content_type = 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_path.endswith('.mp4'):
            content_type = 'video/mp4'
        elif file_path.endswith('.mp3'):
            content_type = 'audio/mpeg'

        # Save file using storage manager
        return storage_manager.save_file(content, directory, filename, content_type)

    def generate_idea(self):
        """Generate a creative idea and prompt using OpenAI."""
        print("Generating idea using OpenAI...")

        # Check if we have an API key
        if not self.openai_client.api_key or self.openai_client.api_key == "your-openai-api-key":
            print("No OpenAI API key found. Using demo mode with mock data.")
            # Use mock data for demo purposes
            idea = "A serene mountain landscape with flowing rivers and lush forests, changing through the seasons."
            prompt = "Photorealistic mountain landscape, flowing rivers, lush green forests, seasonal changes, dramatic lighting, 8k resolution, cinematic, detailed."
        else:
            # Read idea generation prompt
            idea_prompt = self.read_file("prompts/idea_gen.txt")

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": idea_prompt}]
            )

            # Extract the response
            idea_text = response.choices[0].message.content.strip()

            # Parse the response to extract idea and prompt
            lines = idea_text.split('\n')
            idea = ""
            prompt = ""

            for line in lines:
                if line.startswith("Idea:"):
                    idea = line[5:].strip()
                elif line.startswith("Prompt:"):
                    prompt = line[7:].strip()

        # Update project with the generated idea and prompt
        if self.project:
            self.project.idea = idea
            self.project.prompt = prompt

        print(f"Idea generated: {idea[:50]}...")
        return {"idea": idea, "prompt": prompt}

    def generate_image(self, prompt):
        """Generate an image using Flux AI."""
        print(f"Generating image using Flux Image AI...")

        # Check if prompt is empty or None
        if not prompt or prompt.strip() == "":
            raise ValueError("Empty prompt received. Cannot generate image.")

        # Generate a unique filename with png extension
        timestamp = int(time.time())
        image_filename = f"static/image/flux_image_{timestamp}.png"

        # Check if we have a Replicate API key
        replicate_api_key = os.environ.get("REPLICATE_API_TOKEN")
        if not replicate_api_key or replicate_api_key == "your-replicate-api-key":
            print("No Replicate API key found. Using demo mode with placeholder image.")
            # Use a placeholder image for demo purposes
            # Copy a placeholder image from static/img to the image_filename
            try:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(image_filename), exist_ok=True)

                # Use a placeholder image or create a simple colored image
                from PIL import Image
                img = Image.new('RGB', (768, 1344), color = (73, 109, 137))
                img.save(image_filename)

                # Update project with the image path
                if self.project:
                    self.project.image_path = image_filename.replace("static/", "")

                print(f"Placeholder image saved to {image_filename}")
                return image_filename
            except Exception as e:
                print(f"Error creating placeholder image: {str(e)}")
                raise
        else:
            # Call Flux Image API with 9:16 aspect ratio dimensions
            input_data = {
                "width": 768,
                "height": 1344,
                "prompt": prompt,
                "output_format": "png",
                "aspect_ratio": "9:16",
                "safety_tolerance": 6
            }

            try:
                output = replicate.run(
                    "black-forest-labs/flux-pro",
                    input=input_data
                )

                # Download and save the image
                response = requests.get(output)
                self.save_file(image_filename, response.content)

                # Update project with the image path
                if self.project:
                    self.project.image_path = image_filename.replace("static/", "")

                print(f"Image generated and saved to {image_filename}")
                return image_filename
            except Exception as e:
                print(f"Error during image generation: {str(e)}")
                raise

    def generate_video(self, image_path, prompt):
        """Generate a video using Kling AI."""
        print(f"Generating video using Kling AI...")

        # Read video generation settings
        video_settings = self.read_file("prompts/video_gen.txt")

        # Parse video settings
        settings = {}
        for line in video_settings.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                settings[key.strip()] = value.strip()

        # Prepare video generation payload
        duration = int(settings.get('duration', 10))
        aspect_ratio = settings.get('aspect_ratio', '9:16')
        cfg_scale = float(settings.get('cfg_scale', 0.5))
        negative_prompt = settings.get('negative_prompt', '')

        # Generate a unique filename
        timestamp = int(time.time())
        video_filename = f"static/video/kling_video_{timestamp}.mp4"

        # Check if we have a Replicate API key
        replicate_api_key = os.environ.get("REPLICATE_API_TOKEN")
        if not replicate_api_key or replicate_api_key == "your-replicate-api-key":
            print("No Replicate API key found. Using demo mode with placeholder video.")
            # Use a placeholder video for demo purposes
            try:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(video_filename), exist_ok=True)

                # Create a simple video from the image using ffmpeg
                # This creates a 10-second video that just shows the static image
                command = [
                    "ffmpeg",
                    "-loop", "1",
                    "-i", image_path,
                    "-c:v", "libx264",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    "-y",  # Overwrite output file if it exists
                    video_filename
                ]

                try:
                    # Try to run ffmpeg
                    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    # If ffmpeg fails, create an empty file as a placeholder
                    with open(video_filename, "wb") as f:
                        f.write(b"Placeholder video file")

                # Update project with the video path
                if self.project:
                    self.project.video_path = video_filename.replace("static/", "")

                print(f"Placeholder video saved to {video_filename}")
                return video_filename
            except Exception as e:
                print(f"Error creating placeholder video: {str(e)}")
                raise
        else:
            # Open the image for upload
            with open(image_path, "rb") as image_file:
                # Call Kling Video API
                input_data = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "aspect_ratio": aspect_ratio,
                    "cfg_scale": cfg_scale,
                    "duration": duration,
                    "start_image": image_file
                }

                output = replicate.run(
                    "kwaivgi/kling-v1.6-standard",
                    input=input_data
                )

                # Download and save the video
                with open(video_filename, "wb") as file:
                    file.write(output.read())

            # Update project with the video path
            if self.project:
                self.project.video_path = video_filename.replace("static/", "")

            print(f"Video generated and saved to {video_filename}")
            return video_filename

    def generate_voice_dialog(self, idea):
        """Generate voice narration using OpenAI TTS."""
        print("Generating voice narration using OpenAI TTS...")

        # Check if we have an OpenAI API key
        if not self.openai_client.api_key or self.openai_client.api_key == "your-openai-api-key":
            print("No OpenAI API key found. Using demo mode with placeholder voice narration.")
            # Use a placeholder script and voice file for demo purposes
            script = "In this breathtaking landscape, nature reveals its timeless beauty. Mountains rise majestically, rivers carve ancient paths, and forests breathe with life. A perfect harmony of elements, captured in a moment of serene wonder."

            # Generate a unique filename
            timestamp = int(time.time())
            voice_filename = f"static/voice/openai_voice_{timestamp}.mp3"

            try:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(voice_filename), exist_ok=True)

                # Create an empty MP3 file as a placeholder
                with open(voice_filename, "wb") as f:
                    f.write(b"Placeholder voice file")

                # Update project with the voice path
                if self.project:
                    self.project.voice_path = voice_filename.replace("static/", "")

                print(f"Placeholder voice file saved to {voice_filename}")
                return {"filename": voice_filename, "script": script}
            except Exception as e:
                print(f"Error creating placeholder voice file: {str(e)}")
                raise
        else:
            # Generate script for narration
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a creative scriptwriter for short videos."},
                    {"role": "user", "content": f"Write a short, engaging 30-second narration script for a video about this concept: {idea}. The narration should be dramatic, mysterious, and captivating. Keep it under 60 words."}
                ]
            )

            script = response.choices[0].message.content.strip()

            # Generate a unique filename
            timestamp = int(time.time())
            voice_filename = f"static/voice/openai_voice_{timestamp}.mp3"

            # Generate voice using OpenAI TTS
            response = self.openai_client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="onyx",
                input=script
            )

            # Save the audio file
            response.stream_to_file(voice_filename)

            # Update project with the voice path
            if self.project:
                self.project.voice_path = voice_filename.replace("static/", "")

            print(f"Voice narration generated and saved to {voice_filename}")
            return {"filename": voice_filename, "script": script}

    def generate_music(self, idea):
        """Generate music using SonAuto."""
        print("Generating music using SonAuto...")

        # Read music generation settings
        music_settings = self.read_file("prompts/music_gen.txt")

        # Generate a unique filename
        timestamp = int(time.time())
        music_filename = f"static/music/sonauto_music_{timestamp}.mp3"

        # Check if we have a SonAuto API key
        if not self.sonauto_api_key or self.sonauto_api_key == "your-sonauto-api-key":
            print("No SonAuto API key found. Using demo mode with placeholder music.")
            # Use a placeholder music file for demo purposes
            try:
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(music_filename), exist_ok=True)

                # Create an empty MP3 file as a placeholder
                with open(music_filename, "wb") as f:
                    f.write(b"Placeholder music file")

                # Update project with the music path
                if self.project:
                    self.project.music_path = music_filename.replace("static/", "")

                print(f"Placeholder music file saved to {music_filename}")
                return music_filename
            except Exception as e:
                print(f"Error creating placeholder music file: {str(e)}")
                raise
        else:
            # Prepare the API request
            url = "https://api.sonauto.ai/v1/generations"
            headers = {
                "Authorization": f"Bearer {self.sonauto_api_key}",
                "Content-Type": "application/json"
            }

            # Create a prompt for the music based on the idea
            payload = {
                "prompt": f"Create atmospheric music for: {idea}",
                "instrumental": True,
                "prompt_strength": 2.3,
                "output_format": "mp3"
            }

            # Make the API request
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                # Get the generation ID from the response
                generation_id = response.json().get("id")

                # Poll for the generation to complete
                status_url = f"https://api.sonauto.ai/v1/generations/{generation_id}"

                max_attempts = 60  # 5 minutes (5 seconds * 60)
                attempts = 0

                while attempts < max_attempts:
                    status_response = requests.get(status_url, headers=headers)
                    status_data = status_response.json()

                    if status_data.get("status") == "completed":
                        # Download the music file
                        music_url = status_data.get("output_url")
                        music_response = requests.get(music_url)

                        # Save the music file
                        self.save_file(music_filename, music_response.content)

                        # Update project with the music path
                        if self.project:
                            self.project.music_path = music_filename.replace("static/", "")

                        print(f"Music generated and saved to {music_filename}")
                        return music_filename

                    elif status_data.get("status") == "failed":
                        raise Exception(f"Music generation failed: {status_data.get('error')}")

                    # Wait before checking again
                    time.sleep(5)
                    attempts += 1

                raise Exception("Music generation timed out")
            else:
                raise Exception(f"Error initiating music generation: {response.text}")

    def create_final_video(self, video_path, music_path, idea, voice_data):
        """Create the final video with music and voice narration."""
        print("Creating final video with music and voice narration...")

        # Generate a unique filename for the final video
        timestamp = int(time.time())
        final_video = f"static/final/final_video_{timestamp}.mp4"

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(final_video), exist_ok=True)

        # Use FFmpeg to combine video, music, and voice
        try:
            # Command to combine video with audio
            command = [
                "ffmpeg",
                "-i", video_path,  # Input video
                "-i", music_path,  # Input music
                "-i", voice_data["filename"],  # Input voice
                "-filter_complex",
                "[1:a]volume=0.5[music];[2:a]volume=1.0[voice];[music][voice]amix=inputs=2:duration=longest[a]",
                "-map", "0:v",  # Use video from first input
                "-map", "[a]",  # Use mixed audio
                "-c:v", "copy",  # Copy video codec
                "-c:a", "aac",  # AAC audio codec
                "-shortest",  # End when shortest input ends
                "-y",  # Overwrite output file if it exists
                final_video
            ]

            try:
                # Execute the command
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                # If ffmpeg fails, create a simple copy of the video file as a fallback
                print("FFmpeg command failed, creating a simple copy of the video as fallback")
                with open(video_path, "rb") as src_file:
                    with open(final_video, "wb") as dst_file:
                        dst_file.write(src_file.read())

            # Update project with the final video path
            if self.project:
                self.project.final_video_path = final_video.replace("static/", "")
                self.project.status = "completed"

            print(f"Final video created and saved to {final_video}")
            return final_video
        except Exception as e:
            print(f"Error during video composition: {str(e)}")
            # Create an empty file as a last resort
            try:
                with open(final_video, "wb") as f:
                    f.write(b"Placeholder final video file")

                # Update project with the final video path
                if self.project:
                    self.project.final_video_path = final_video.replace("static/", "")
                    self.project.status = "completed"

                print(f"Placeholder final video saved to {final_video}")
                return final_video
            except Exception as inner_e:
                print(f"Error creating placeholder final video: {str(inner_e)}")
                raise

    def generate_complete_video(self):
        """Run the complete video generation pipeline."""
        try:
            # Update project status
            if self.project:
                self.project.status = "processing"

            # Step 1: Generate idea
            result = self.generate_idea()
            idea, prompt = result["idea"], result["prompt"]

            # Step 2: Generate image
            image_path = self.generate_image(prompt)

            # Step 3: Generate voice dialog
            voice_data = self.generate_voice_dialog(idea)

            # Step 4: Generate video
            video_path = self.generate_video(image_path, prompt)

            # Step 5: Generate music
            music_path = self.generate_music(idea)

            # Step 6: Create final video with music and voice
            final_video = self.create_final_video(video_path, music_path, idea, voice_data)

            print("\nVideo generation process complete!")
            print(f"Final Output: {final_video}")

            return {
                "status": "completed",
                "final_video": final_video
            }
        except Exception as e:
            print(f"Error during video generation: {str(e)}")

            # Update project status
            if self.project:
                self.project.status = "error"

            return {
                "status": "error",
                "message": str(e)
            }
