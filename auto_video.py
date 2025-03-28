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

# Constants for the idea logging system
LAST_IDEAS_FILE = "last_ideas.json"
MAX_STORED_IDEAS = 6

def read_file(file_path):
    """Read the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

def save_file(file_path, content, mode='wb'):
    """Save content to a file."""
    with open(file_path, mode) as file:
        file.write(content)

def load_last_ideas():
    """Load the list of recently generated ideas."""
    if os.path.exists(LAST_IDEAS_FILE):
        try:
            with open(LAST_IDEAS_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            # If the file exists but is corrupted, return an empty list
            return []
    return []

def save_idea_to_history(idea):
    """Save an idea to the history file, keeping only the most recent ones."""
    ideas = load_last_ideas()
    
    # Add the new idea
    ideas.append(idea)
    
    # Keep only the most recent MAX_STORED_IDEAS
    if len(ideas) > MAX_STORED_IDEAS:
        ideas = ideas[-MAX_STORED_IDEAS:]
    
    # Save the updated list
    with open(LAST_IDEAS_FILE, 'w') as file:
        json.dump(ideas, file)

def generate_idea():
    """Step 1: Generate an idea using OpenAI API, avoiding recent ideas."""
    print("Step 1: Generating idea using OpenAI API...")
    
    # Read prompt from idea_gen.txt
    idea_prompt = read_file("prompts/idea_gen.txt")
    
    # Load recently used ideas
    last_ideas = load_last_ideas()
    
    # Add context about avoiding recent ideas if there are any
    if last_ideas:
        avoid_context = "\n\nPlease avoid generating ideas similar to these recently created ones:\n"
        for i, idea in enumerate(last_ideas):
            avoid_context += f"{i+1}. {idea}\n"
        
        # Append the avoidance context to the prompt
        idea_prompt += avoid_context
    
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
    
    # Save the new idea to history
    save_idea_to_history(idea)
    
    return {"idea": idea, "prompt": prompt}

def generate_image(prompt):
    """Step 2: Generate an image using Flux AI."""
    print(f"Step 2: Generating image using Flux Image AI with prompt: {prompt[:50]}...")
    
    # Check if prompt is empty or None
    if not prompt or prompt.strip() == "":
        print("Warning: Empty prompt detected. Using a fallback prompt.")
        prompt = "A mysterious atmospheric scene with dramatic lighting and cinematic composition."
    
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
    
    try:
        output = replicate.run(
            "black-forest-labs/flux-pro",
            input=input_data
        )
        
        # Download and save the image
        response = requests.get(output)
        save_file(image_filename, response.content)
        
        print(f"Image generated and saved to {image_filename}")
        return image_filename
    except Exception as e:
        print(f"Error during image generation: {str(e)}")
        print("Trying again with simplified prompt...")
        
        # Try again with a simplified prompt
        simplified_prompt = prompt.split('.')[0] if '.' in prompt else prompt[:100]
        input_data["prompt"] = simplified_prompt
        
        try:
            output = replicate.run(
                "black-forest-labs/flux-pro",
                input=input_data
            )
            
            # Download and save the image
            response = requests.get(output)
            save_file(image_filename, response.content)
            
            print(f"Image generated and saved to {image_filename}")
            return image_filename
        except Exception as e2:
            print(f"Second attempt failed: {str(e2)}")
            raise

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
    duration = int(settings.get('duration', 10))
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
        "tags": ["ethereal", "chants", "folklore", "ancient", "spiritual", "ambient", "ritualistic"],
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

def generate_voice_dialog(idea):
    """Generate a short dialog that fits the idea using OpenAI's GPT-4o model and TTS."""
    print(f"Generating voice dialog for idea: {idea[:50]}...")
    
    # Read voice examples to use as references
    voice_examples = read_file("prompts/voice_examples.txt")
    
    # Create prompt for generating the dialog with clearer instructions
    dialog_prompt = f"""
    Create a short, engaging single line of dialog question (maximum 15 words) for the following idea:

    Idea: 
    \n\n
    {idea}
    \n\n
    This short dialog question should be something a character might say when experiencing this scene.
    It should be brief, impactful, like the examples:
     "I wonder what happened here...?", "What could be over there...?", "I wonder where Queen Cleopatra is buried...?" or "What is that sound...?"

    In the dialog question, avoid cringe cliche terms like "secrets", "unveil", "moon", "breath etc. Please be creative and inspired by the idea.
    
    Also determine whether this dialog questions would best be spoken by a male voice (Ballad) or female voice (Shimmer) based on the archetype of the idea.
    
    IMPORTANT: You MUST provide detailed voice instructions that describe how the line should be delivered.
    
    Here are some examples of good voice instructions:

    {voice_examples}

    Create detailed voice instructions similar to these examples that fit the idea and the dialog.

    Your response MUST follow this exact format:
    Voice: [Ballad or Shimmer] (based on the archetype of the idea)
    Dialog: [the dialog question]
    Instructions: [detailed speaking instructions including tone, emotion, pacing, emphasis, etc.]
    """
    
    # Call OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": dialog_prompt
            }
        ]
    )
    
    result = response.choices[0].message.content
    print(f"Raw result from GPT:\n{result}")  # Debug line
    
    # Parse the result with more robust handling
    voice = "onyx"  # Default male voice
    dialog = ""
    instructions = "Speak naturally with appropriate emotion."
    
    # Extract values from the response with more robust handling
    lines = result.split('\n')
    for i, line in enumerate(lines):
        if line.lower().startswith("voice:"):
            voice_value = line.replace("Voice:", "", 1).strip().lower()
            # Only accept onyx or shimmer
            if "shimmer" in voice_value:
                voice = "shimmer"
                
        elif line.lower().startswith("dialog:"):
            dialog = line.replace("Dialog:", "", 1).strip()
            # Remove extra quotes if present
            if dialog.startswith('"') and dialog.endswith('"'):
                dialog = dialog[1:-1]
                
        elif line.lower().startswith("instructions:"):
            # Grab the instructions part, which might span multiple lines
            instructions_parts = [line.replace("Instructions:", "", 1).strip()]
            
            # Check if there are more lines after "Instructions:" that are part of the instructions
            for j in range(i+1, len(lines)):
                next_line = lines[j].strip()
                # Stop if we hit a new section
                if next_line.lower().startswith("voice:") or next_line.lower().startswith("dialog:"):
                    break
                if next_line:  # Only add non-empty lines
                    instructions_parts.append(next_line)
                    
            instructions = " ".join(instructions_parts).strip()
    
    # Fallback if instructions are still empty
    if not instructions or instructions.strip() == "":
        print("Warning: No instructions detected. Using fallback instructions.")
        instructions = "Speak with emotion and emphasis appropriate to the scene, maintaining a natural cadence and clear articulation."
    
    print(f"Generated dialog: '{dialog}' with voice '{voice}'")
    print(f"Voice instructions: {instructions}")
    
    # Ensure voice directory exists
    Path("voice").mkdir(exist_ok=True)
    
    # Generate a unique filename
    timestamp = int(time.time())
    voice_filename = f"voice/openai_voice_{timestamp}.mp3"
    
    # Generate the speech using OpenAI TTS
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=dialog,
        instructions=instructions
    )
    
    # Save the audio file
    response.stream_to_file(voice_filename)
    
    print(f"Voice dialog generated and saved to {voice_filename}")
    return {
        "filename": voice_filename, 
        "dialog": dialog, 
        "voice": voice, 
        "instructions": instructions
    }

def create_final_video(video_path, music_path, idea, voice_data=None):
    """Merge video with music and voice dialog using FFMPEG."""
    print("Creating final video with music and voice...")
    
    # Generate output filename
    output_filename = "final_output.mp4"
    
    # Base FFMPEG command for merging video and music
    ffmpeg_cmd = (
        f'ffmpeg -y -i "{video_path}" -i "{music_path}" '
    )
    
    # Add voice input if available
    if voice_data and os.path.exists(voice_data["filename"]):
        ffmpeg_cmd += f'-i "{voice_data["filename"]}" '
        # Map all streams - video from first input, music from second, voice from third
        # Apply a 1-second delay to the voice track using the adelay filter
        # Adjust volume levels: music at 0.4 (reduced) and voice at 1.5 (amplified)
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" -shortest -t 10 '
        )
    else:
        # Just map video and music without voice
        ffmpeg_cmd += f'-map 0:v -map 1:a -shortest -t 10 '
    
    # Finish the command with codec settings and output file
    ffmpeg_cmd += f'-c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
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

        # Step 3: Generate voice dialog
        voice_data = generate_voice_dialog(idea)
        
        # Step 4: Generate video
        video_path = generate_video(image_path, prompt)
        
        # Step 5: Generate music
        music_path = generate_music(idea)
        
        print(f"Using video file: {video_path}")
        print(f"Using music file: {music_path}")
        print(f"Using voice file: {voice_data['filename']}")
        
        # Step 6: Create final video with music and voice
        final_video = create_final_video(video_path, music_path, idea, voice_data)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Idea: {idea}")
        print(f"Generated Image: {image_path}")
        print(f"Generated Video: {video_path}")
        print(f"Generated Music: {music_path}")
        print(f"Generated Voice: {voice_data['filename']}")
        print(f"Voice Dialog: {voice_data['dialog']} (Voice: {voice_data['voice']})")
        print(f"Final Output: {final_video}")
        
    except Exception as e:
        print(f"Error in content generation pipeline: {str(e)}")
        print("Process failed. Please try running the script again.")

if __name__ == "__main__":
    # Import OpenAI here to avoid potential circular import issues
    from openai import OpenAI
    main()
