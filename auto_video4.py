import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
SONAUTO_API_KEY = os.getenv("SONAUTO_API_KEY")

def read_file(file_path):
    """Read the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def save_file(file_path, content, mode='wb'):
    """Save content to a file."""
    with open(file_path, mode) as file:
        file.write(content)

def generate_music(idea):
    """Generate music using Sonauto."""
    print(f"Generating music using Sonauto...")
    
    # Read music generation settings
    music_settings_text = read_file("prompts/music_gen.txt")
    
    # Set default values
    prompt_strength = 2.3
    
    # Extract prompt_strength if present in the settings
    if "prompt_strength" in music_settings_text:
        try:
            prompt_strength_line = [line for line in music_settings_text.split('\n') if "prompt_strength" in line][0]
            prompt_strength_str = prompt_strength_line.split(':', 1)[1].strip()
            prompt_strength_str = prompt_strength_str.split('(default:', 1)[1].split(')', 1)[0].strip() if '(default:' in prompt_strength_str else prompt_strength_str
            prompt_strength = float(prompt_strength_str)
        except:
            prompt_strength = 2.3
    
    # Prepare the prompt for music generation
    music_prompt = idea
    
    # Generate a unique filename
    timestamp = int(time.time())
    music_filename = f"music/sonauto_music_{timestamp}.mp3"
    
    # Prepare the request payload with fixed tags
    payload = {
        "prompt": music_prompt,
        "tags": ["gregorian chant","horror", "religious"],
        "instrumental": True,
        "prompt_strength": prompt_strength,
        "output_format": "mp3"
    }
    
    # Call Sonauto API
    headers = {
        "Authorization": f"Bearer {SONAUTO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Start generation
    response = requests.post(
        "https://api.sonauto.ai/v1/generations",
        json=payload,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error generating music: {response.text}")
        return None
    
    task_id = response.json()["task_id"]
    print(f"Music generation started with task ID: {task_id}")
    
    # Step 2: Wait for generation to complete
    status = ""
    while status != "SUCCESS":
        time.sleep(5)  # Wait 5 seconds between checks
        
        status_response = requests.get(
            f"https://api.sonauto.ai/v1/generations/status/{task_id}",
            headers=headers
        )
        
        if status_response.status_code != 200:
            print(f"Error checking music generation status: {status_response.text}")
            return None
        
        status = status_response.text.strip('"')
        print(f"Music generation status: {status}")
        
        if status == "FAILURE":
            print("Music generation failed")
            return None
        
        if status == "SUCCESS":
            # Get the generated music URL
            result_response = requests.get(
                f"https://api.sonauto.ai/v1/generations/{task_id}",
                headers=headers
            )
            
            if result_response.status_code != 200:
                print(f"Error getting music URL: {result_response.text}")
                return None
            
            song_url = result_response.json()["song_paths"][0]
            
            # Download the music file
            music_response = requests.get(song_url)
            save_file(music_filename, music_response.content)
            
            print(f"Music generated and saved to {music_filename}")
            break
    
    return music_filename

def merge_videos(video_paths, music_path, voice_path):
    """Merge videos with music and voice dialog using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music and voice...")
    
    # Make sure all files exist
    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
    
    # Check if music path is valid
    has_music = music_path and os.path.exists(music_path)
    if not has_music:
        print("Warning: Music file not found. Creating video without music.")
    else:
        print(f"Using music file: {music_path}")
    
    # Check if voice path is valid
    has_voice = voice_path and os.path.exists(voice_path)
    if not has_voice:
        print("Warning: Voice file not found. Creating video without narration.")
    else:
        print(f"Using voice file: {voice_path}")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # Create a temporary file for concatenation
    with open("temp_list.txt", "w") as f:
        for video_path in video_paths:
            f.write(f"file '{video_path}'\n")
    
    # First concatenate the videos
    concat_output = "temp_concat.mp4"
    concat_cmd = f'ffmpeg -y -f concat -safe 0 -i temp_list.txt -c copy {concat_output}'
    
    print(f"Running video concatenation command: {concat_cmd}")
    concat_result = os.system(concat_cmd)
    
    if concat_result != 0:
        print(f"Error concatenating videos. Exit code: {concat_result}")
        return None
    
    # Now add music and voice to the concatenated video
    ffmpeg_cmd = f'ffmpeg -y -i "{concat_output}" '
    
    # Add input files if available
    if has_music:
        ffmpeg_cmd += f'-i "{music_path}" '
    
    if has_voice:
        ffmpeg_cmd += f'-i "{voice_path}" '
    
    # Set up audio filtering based on available inputs
    if has_music and has_voice:
        # Both music and voice available
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];'
            f'[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" '
        )
    elif has_music:
        # Only music available
        ffmpeg_cmd += f'-filter_complex "[1:a]volume=0.4[a]" -map 0:v -map "[a]" '
    elif has_voice:
        # Only voice available
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]adelay=1000|1000,volume=1.5[a]" '
            f'-map 0:v -map "[a]" '
        )
    else:
        # No audio, just use video
        ffmpeg_cmd += f'-map 0:v '
    
    # Set duration and finishing options
    ffmpeg_cmd += f'-shortest -t 30 -c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
    # Print the command for debugging
    print(f"Running FFMPEG command: {ffmpeg_cmd}")
    
    # Execute FFMPEG command
    result = os.system(ffmpeg_cmd)
    
    # Clean up temporary files
    try:
        os.remove("temp_list.txt")
        os.remove(concat_output)
    except:
        pass
    
    if result == 0:
        print(f"Final video created successfully: {output_filename}")
        return output_filename
    else:
        print(f"Error creating final video. Exit code: {result}")
        return None

def main():
    # Provide the Noppera-bō idea text for music generation
    idea = "The Discordant Paraclete is an ancient, accursed entity chronicled in forbidden religious manuscripts."
    
    # Generate music
    music_path = generate_music(idea)
    
    # Video paths from the previous run
    video_paths = [
        "video/kling_video_1743059223.mp4", 
        "video/kling_video_1743059442.mp4", 
        "video/kling_video_1743059651.mp4"
    ]
    
    # Voice path from the previous run
    voice_path = "voice/openai_voice_1743059216.mp3"
    
    # Merge videos
    final_video = merge_videos(video_paths, music_path, voice_path)
    
    print("\nProcess Complete!")
    if final_video:
        print(f"Final Output: {final_video}")

if __name__ == "__main__":
    main()