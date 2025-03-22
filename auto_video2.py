import os
import base64
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import replicate

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SONAUTO_API_KEY = os.getenv("SONAUTO_API_KEY")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

# Set Replicate API key for the replicate client
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

# Ensure output directories exist
Path("image").mkdir(exist_ok=True)
Path("video").mkdir(exist_ok=True)
Path("music").mkdir(exist_ok=True)

def read_file(file_path):
    """Read the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def save_file(file_path, content, mode='wb'):
    """Save content to a file."""
    with open(file_path, mode) as file:
        file.write(content)

def generate_idea():
    """Step 1: Generate an idea using OpenAI API."""
    print("Step 1: Generating idea using OpenAI API...")
    
    # Read prompt from idea_gen.txt
    idea_prompt = read_file("prompts/idea_gen.txt")
    
    # Call OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": idea_prompt
            }
        ]
    )
    
    # Parse the result to get idea and prompt
    result = response.choices[0].message.content
    
    
    # Parse the result to extract idea and prompt
    # Format expected: "Idea: [idea text]\nPrompt: [prompt text]"
    parts = result.split("Prompt:")
    
    # Clean up the idea text
    idea = parts[0].replace("Idea:", "").strip()
    
    
    # Remove "Example X:" if present
    if "Example" in idea and ":" in idea.split("Example")[1]:
        # Find where the actual POV text starts
        try:
            example_parts = idea.split(":", 1)
            if len(example_parts) > 1:
                # Take only the part after "Example X:"
                idea = example_parts[1].strip()
        except:
            # If parsing fails, keep the original idea
            pass
    
    # Remove markdown formatting (asterisks for bold/italic)
    idea = idea.replace('*', '')
    # Remove any extra newlines or unnecessary whitespace
    idea = ' '.join(idea.split())
    
    prompt = parts[1].strip() if len(parts) > 1 else ""
    
    print(f"Generated Idea: {idea}")
    print(f"Generated Prompt: {prompt}")
    
    return {"idea": idea, "prompt": prompt}

def generate_image(prompt):
    """Step 2: Generate an image using Flux AI."""
    print(f"Step 2: Generating image using Flux Image AI with prompt: {prompt[:50]}...")
    
    # Generate a unique filename with png extension
    timestamp = int(time.time())
    image_filename = f"image/flux_image_{timestamp}.png"
    
    # Call Flux Image API with 9:16 aspect ratio dimensions
    # and explicitly requesting PNG output
    input_data = {
        "width": 768,
        "height": 1344,
        "prompt": prompt,
        "output_format": "png",  # Explicitly request PNG format
        "aspect_ratio": "9:16",  # Explicitly set aspect ratio to 9:16
        "safety_tolerance": 6    # Set safety tolerance to maximum (6)
    }
    
    output = replicate.run(
        "black-forest-labs/flux-pro",
        input=input_data
    )
    
    # Download and save the image
    response = requests.get(output)
    save_file(image_filename, response.content)
    
    print(f"Image generated and saved to {image_filename}")
    return image_filename

def generate_video(image_path, prompt):
    """Step 3: Generate a video using Kling AI."""
    print(f"Step 3: Generating video using Kling AI...")
    
    # Read video generation settings
    video_settings = read_file("prompts/video_gen.txt")
    
    # Parse video settings
    settings = {}
    for line in video_settings.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            settings[key.strip()] = value.strip()
    
    # Prepare video generation payload
    duration = int(settings.get('duration', 8))
    aspect_ratio = settings.get('aspect_ratio', '9:16')
    cfg_scale = float(settings.get('cfg_scale', 0.5))
    negative_prompt = settings.get('negative_prompt', '')
    
    # Generate a unique filename
    timestamp = int(time.time())
    video_filename = f"video/kling_video_{timestamp}.mp4"
    
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
    
    print(f"Video generated and saved to {video_filename}")
    return video_filename

def generate_music(idea):
    """Step 4: Generate music using Sonauto."""
    print(f"Step 4: Generating music using Sonauto...")
    
    # Read music generation settings - these are example settings, not actual JSON
    # We'll extract the prompt_strength value from the text
    music_settings_text = read_file("prompts/music_gen.txt")
    
    # Set default values
    prompt_strength = 2.3
    
    # Extract prompt_strength if present in the settings
    if "prompt_strength" in music_settings_text:
        try:
            # Try to extract the float value from the string
            prompt_strength_line = [line for line in music_settings_text.split('\n') if "prompt_strength" in line][0]
            prompt_strength_str = prompt_strength_line.split(':', 1)[1].strip()
            prompt_strength_str = prompt_strength_str.split('(default:', 1)[1].split(')', 1)[0].strip() if '(default:' in prompt_strength_str else prompt_strength_str
            prompt_strength = float(prompt_strength_str)
        except:
            # If parsing fails, use the default
            prompt_strength = 2.3
    
    # Prepare the prompt for music generation
    music_prompt = idea
    
    # Generate a unique filename
    timestamp = int(time.time())
    music_filename = f"music/sonauto_music_{timestamp}.mp3"
    
    # Prepare the request payload
    payload = {
        "prompt": music_prompt,
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

def create_final_video(video_path, music_path, idea):
    """Merge video with music using FFMPEG."""
    print("Creating final video with music...")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # FFMPEG command without captions - just merging video and audio
    ffmpeg_cmd = (
        f'ffmpeg -y -i "{video_path}" -i "{music_path}" '
        f'-map 0:v -map 1:a -shortest -t 10 '
        f'-c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    )
    
    # Print the command for debugging
    print(f"Running FFMPEG command: {ffmpeg_cmd}")
    
    # Execute FFMPEG command
    result = os.system(ffmpeg_cmd)
    
    if result == 0:
        print(f"Final video created successfully: {output_filename}")
        return output_filename
    else:
        print(f"Error creating final video. Exit code: {result}")
        return None

def main():
    """Main function to run the full content generation pipeline."""
    try:
        # Step 1: Generate idea
        result = generate_idea()
        idea, prompt = result["idea"], result["prompt"]
        
        # Step 2: Generate image
        image_path = generate_image(prompt)
        
        # Step 3: Generate video
        video_path = generate_video(image_path, prompt)
        
        # Step 4: Generate music
        music_path = generate_music(idea)
        
        print(f"Using video file: {video_path}")
        print(f"Using music file: {music_path}")
        
        # Step 5: Create final video with music
        final_video = create_final_video(video_path, music_path, idea)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Idea: {idea}")
        print(f"Generated Image: {image_path}")
        print(f"Generated Video: {video_path}")
        print(f"Generated Music: {music_path}")
        print(f"Final Output: {final_video}")
        
    except Exception as e:
        print(f"Error in content generation pipeline: {str(e)}")
        print("Process failed. Please try running the script again.")

def test_ffmpeg_captions():
    """Test FFMPEG caption functionality without running the full generation pipeline."""
    print("Testing FFMPEG caption functionality...")
    
    # Look for existing video files in the video folder
    video_folder = Path("video")
    video_files = list(video_folder.glob("*.mp4"))
    
    # Look for existing music files in the music folder
    music_folder = Path("music")
    music_files = list(music_folder.glob("*.mp3"))
    
    if not video_files:
        print("Error: No video files found in the 'video' folder.")
        print("Please run the video generation step first or add a video file manually.")
        return
    
    if not music_files:
        print("Error: No music files found in the 'music' folder.")
        print("Please run the music generation step first or add a music file manually.")
        return
    
    # Use the most recent files
    video_path = str(sorted(video_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    music_path = str(sorted(music_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    
    print(f"Using existing video: {video_path}")
    print(f"Using existing music: {music_path}")
    
    # Test idea text
    idea = "POV: You are a exiled wizard in a ancitent forrest, England 1655"
    
    # Call the final video creation function
    final_video = create_final_video(video_path, music_path, idea)
    
    if final_video:
        print(f"Test completed successfully! Output saved to: {final_video}")
    else:
        print("Test failed. Check the error messages above.")

# Add this at the end of the file to run the test function directly
if __name__ == "__main__":
    # Import OpenAI here to avoid potential circular import issues
    from openai import OpenAI
    
    # Comment out main() and uncomment test_ffmpeg_captions() to test just the FFMPEG part
    # main()
    test_ffmpeg_captions()
