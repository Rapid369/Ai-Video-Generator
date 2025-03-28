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
LAST_IDEAS_FILE = "last_ideas2.json"
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
    idea_prompt = read_file("prompts/idea_gen2.txt")
    
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
        model="o3-mini",
        messages=[
            {
                "role": "user",
                "content": idea_prompt
            }
        ]
    )
    
    # Parse the result to get idea and prompt
    result = response.choices[0].message.content
    
    # Extract idea and prompt parts
    idea_part = ""
    prompt_part = ""
    
    # Check if result contains "FACT:" and "PROMPT:" structure
    if "FACT:" in result and "PROMPT:" in result:
        # Format: "## X. Title\nFACT: ...\nPROMPT: ..."
        idea_parts = result.split("PROMPT:")
        idea_part = idea_parts[0].strip()
        prompt_part = idea_parts[1].strip() if len(idea_parts) > 1 else ""
    else:
        # Try the older format: "Idea: ...\nPrompt: ..."
        parts = result.split("Prompt:")
        idea_part = parts[0].replace("Idea:", "").strip()
        prompt_part = parts[1].strip() if len(parts) > 1 else ""
    
    # Clean up idea text
    # Remove "Example X:" if present
    if "Example" in idea_part and ":" in idea_part.split("Example")[1]:
        try:
            example_parts = idea_part.split(":", 1)
            if len(example_parts) > 1:
                idea_part = example_parts[1].strip()
        except:
            pass
    
    # Remove markdown formatting
    idea_part = idea_part.replace('*', '')
    idea_part = ' '.join(idea_part.split())
    
    # If prompt is empty, extract it from the idea
    if not prompt_part or prompt_part.strip() == "":
        if "Point of view" in idea_part:
            # Try to extract the prompt directly from the idea text
            prompt_index = idea_part.find("Point of view")
            if prompt_index > 0:
                prompt_part = idea_part[prompt_index:].strip()
                print("Extracted prompt from idea text.")
    
    # Final fallback - if prompt is still empty, use the idea as the prompt
    if not prompt_part or prompt_part.strip() == "":
        prompt_part = f"A mystical, cinematic scene depicting {idea_part}"
        print("Using fallback prompt based on idea.")
    
    print(f"Generated Idea: {idea_part}")
    print(f"Generated Prompt: {prompt_part}")
    
    # Save the new idea to history
    save_idea_to_history(idea_part)
    
    return {"idea": idea_part, "prompt": prompt_part}

def generate_second_prompt(idea, first_prompt):
    """Generate a second complementary prompt for the same idea."""
    print("Generating second complementary prompt...")
    
    # Create a prompt to ask for a complementary scene
    second_prompt_request = f"""
    Based on the following idea and first prompt, create a SECOND complementary prompt that shows a different aspect or moment related to the same horror concept.
    
    IDEA: {idea}
    
    FIRST PROMPT: {first_prompt}
    
    Create a SECOND prompt that:
    1. Maintains the same horror concept but shows a different scene/moment
    2. Include captured digitally with examples like "RED Komodo 6K and anamorphic lenses" or "Sony FX9 and vintage cine lenses" or similar professional camera setups
    3. MUST prominently feature a close-up of a woman's face showing intense terror and despair as she encounters or reacts to the horrifying entity/demon/creature
    4. Include specific details about the woman's expressions (e.g., wide eyes, trembling lips, tears streaming down her face)
    5. Uses the same visual style but shows the horrifying entity/creature in frame causing her terror
    6. Would work well as a second scene in a short video about this horror
    7. Has a natural transition potential from/to the first scene
    
    Format your response as a single detailed prompt paragraph only, similar in structure to the first prompt.
    """
    
    # Call OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": second_prompt_request
            }
        ]
    )
    
    # Get the second prompt
    second_prompt = response.choices[0].message.content.strip()
    
    # Clean up potential formatting
    if second_prompt.startswith("PROMPT:"):
        second_prompt = second_prompt.replace("PROMPT:", "", 1).strip()
    
    print(f"Generated Second Prompt: {second_prompt[:100]}...")
    return second_prompt

def generate_third_prompt(idea, first_prompt, second_prompt):
    """Generate a third complementary prompt for the same idea."""
    print("Generating third complementary prompt...")
    
    # Create a prompt to ask for a third complementary scene
    third_prompt_request = f"""
    Based on the following idea and existing prompts, create a THIRD complementary prompt that shows the final aspect or culmination related to the same horror concept.
    
    IDEA: {idea}
    
    FIRST PROMPT: {first_prompt}
    
    SECOND PROMPT: {second_prompt}
    
    Create a THIRD prompt that:
    1. Maintains the same horror concept but shows the final or climactic scene
    2. Include captured digitally with examples like "RED Komodo 6K and anamorphic lenses" or "Sony FX9 and vintage cine lenses" or similar professional camera setups
    3. MUST feature an intense close-up shot of the woman's face in absolute terror and despair at the climactic moment
    4. Include vivid details of her facial expressions showing pure horror (e.g., bloodshot eyes, mascara-stained tears, contorted features)
    5. Show the horrifying entity/demon/creature in its most terrifying form as it claims its victim
    6. Uses the same visual style as the previous prompts including ultra realistic details
    7. Would work well as the conclusion of a short horror video trilogy
    8. Has a natural transition from the second scene
    9. Provides a shocking and horrifying final revelation
    
    Format your response as a single detailed prompt paragraph only, similar in structure to the previous prompts.
    """
    
    # Call OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": third_prompt_request
            }
        ]
    )
    
    # Get the third prompt
    third_prompt = response.choices[0].message.content.strip()
    
    # Clean up potential formatting
    if third_prompt.startswith("PROMPT:"):
        third_prompt = third_prompt.replace("PROMPT:", "", 1).strip()
    
    print(f"Generated Third Prompt: {third_prompt[:100]}...")
    return third_prompt

def generate_image(prompt):
    """Step 2: Generate an image using Flux AI."""
    print(f"Step 2: Generating image using Flux Image AI with prompt: {prompt[:50]}...")
    
    # Check if prompt is empty or None
    if not prompt or prompt.strip() == "":
        raise ValueError("Empty prompt received. Cannot generate image.")
    
    # Generate a unique filename with png extension
    timestamp = int(time.time())
    image_filename = f"image/flux_image_{timestamp}.png"
    
    # Call Flux Image API with 9:16 aspect ratio dimensions
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
        raise  # Re-raise the exception to stop the script

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
        "tags": ["horror", "chants", "suspenseful", "scary"],
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
    """Generate voice narration using the exact FACT from the idea."""
    print(f"Generating voice narration for folklore FACT...")
    
    # Extract the FACT from the idea text
    fact = ""
    if "FACT:" in idea:
        # Extract everything after "FACT:" and before any next section
        fact_section = idea.split("FACT:")[1].strip()
        # If there are other sections after the FACT, only take the FACT part
        if "PROMPT:" in fact_section:
            fact = fact_section.split("PROMPT:")[0].strip()
        else:
            fact = fact_section
    else:
        # If no FACT label, use the entire idea as the fact
        fact = idea
    
    # Clean up the fact text
    fact = fact.strip()
    
    # Ensure we have content
    if not fact:
        fact = idea  # Fallback to the entire idea text if extraction failed
    
    print(f"Extracted FACT for narration: {fact}")
    
    # Read voice examples to use as references
    voice_examples = read_file("prompts/voice_examples.txt")
    
    # Create prompt for generating voice instructions only
    voice_prompt = f"""
    I need appropriate voice instructions for narrating this horror urban legend FACT:
    
    "{fact}"
    
    The narration will use the EXACT text above, word for word. I just need you to:
    
    1. Determine if this should be spoken by a male voice (Ballad) or female voice (Shimmer)
    2. Provide detailed voice instructions that will make this fact engaging when narrated
    
    Here are some examples of good voice instructions:
    {voice_examples}
    
    Your response MUST follow this exact format:
    Voice: [Ballad or Shimmer]
    Instructions: [detailed speaking instructions including tone, emotion, pacing, emphasis, etc.]
    """
    
    # Call OpenAI API just for voice selection and instructions
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": voice_prompt
            }
        ]
    )
    
    result = response.choices[0].message.content
    print(f"Raw voice instructions from GPT:\n{result}")
    
    # Parse the result
    voice = "onyx"  # Default male voice
    instructions = "Speak clearly with a measured pace, emphasizing key folklore elements."
    
    # Extract values from the response
    lines = result.split('\n')
    for i, line in enumerate(lines):
        if line.lower().startswith("voice:"):
            voice_value = line.replace("Voice:", "", 1).strip().lower()
            if "shimmer" in voice_value:
                voice = "shimmer"
                
        elif line.lower().startswith("instructions:"):
            # Grab the instructions part, which might span multiple lines
            instructions_parts = [line.replace("Instructions:", "", 1).strip()]
            
            # Check if there are more lines after "Instructions:" that are part of the instructions
            for j in range(i+1, len(lines)):
                next_line = lines[j].strip()
                # Stop if we hit a new section
                if next_line.lower().startswith("voice:"):
                    break
                if next_line:  # Only add non-empty lines
                    instructions_parts.append(next_line)
                    
            instructions = " ".join(instructions_parts).strip()
    
    print(f"Using FACT as dialog: '{fact}'")
    print(f"Selected voice: '{voice}'")
    print(f"Voice instructions: {instructions}")
    
    # Ensure voice directory exists
    Path("voice").mkdir(exist_ok=True)
    
    # Generate a unique filename
    timestamp = int(time.time())
    voice_filename = f"voice/openai_voice_{timestamp}.mp3"
    
    # Generate the speech using OpenAI TTS with the FACT as the exact input
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=fact,  # Use the exact FACT text
        instructions=instructions
    )
    
    # Save the audio file
    response.stream_to_file(voice_filename)
    
    print(f"Voice narration generated and saved to {voice_filename}")
    return {
        "filename": voice_filename, 
        "dialog": fact,  # The exact FACT text used as dialog
        "voice": voice, 
        "instructions": instructions
    }

def merge_videos(video_paths, music_path, voice_data=None):
    """Merge videos with music and voice dialog using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music and voice...")
    
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
    ffmpeg_cmd = (
        f'ffmpeg -y -i "{concat_output}" -i "{music_path}" '
    )
    
    # Add voice input if available
    if voice_data and os.path.exists(voice_data["filename"]):
        ffmpeg_cmd += f'-i "{voice_data["filename"]}" '
        # Map all streams - video from first input, music from second, voice from third
        # Apply a 1-second delay to the voice track using the adelay filter
        # Adjust volume levels: music at 0.4 (reduced) and voice at 1.5 (amplified)
        ffmpeg_cmd += (
            f'-filter_complex "[1:a]volume=0.4[music];[2:a]adelay=1000|1000,volume=1.5[voice];[music][voice]amix=inputs=2:duration=longest[a]" '
            f'-map 0:v -map "[a]" -shortest -t 30 '
        )
    else:
        # Just map video and music without voice
        ffmpeg_cmd += f'-map 0:v -map 1:a -shortest -t 30 '
    
    # Finish the command with codec settings and output file
    ffmpeg_cmd += f'-c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
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
    """Main function to run the full content generation pipeline."""
    try:
        # Step 1: Generate idea
        result = generate_idea()
        idea, prompt1 = result["idea"], result["prompt"]
        
        # Step 2: Generate two more complementary prompts
        prompt2 = generate_second_prompt(idea, prompt1)
        prompt3 = generate_third_prompt(idea, prompt1, prompt2)
        
        # Step 3: Generate images for all three prompts
        image_path1 = generate_image(prompt1)
        image_path2 = generate_image(prompt2)
        image_path3 = generate_image(prompt3)

        # Step 4: Generate voice dialog
        voice_data = generate_voice_dialog(idea)
        
        # Step 5: Generate videos from all three images
        video_path1 = generate_video(image_path1, prompt1)
        video_path2 = generate_video(image_path2, prompt2)
        video_path3 = generate_video(image_path3, prompt3)
        
        # Step 6: Generate music
        music_path = generate_music(idea)
        
        print(f"Using video files: {video_path1}, {video_path2}, and {video_path3}")
        print(f"Using music file: {music_path}")
        print(f"Using voice file: {voice_data['filename']}")
        
        # Step 7: Merge videos with music and voice
        video_paths = [video_path1, video_path2, video_path3]
        final_video = merge_videos(video_paths, music_path, voice_data)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Idea: {idea}")
        print(f"Generated Images: {image_path1}, {image_path2}, and {image_path3}")
        print(f"Generated Videos: {video_path1}, {video_path2}, and {video_path3}")
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
