import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import replicate
import cv2

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
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

def extract_last_frame(video_path, output_path):
    """
    Extract the last frame from a video file and save it as an image.
    
    Args:
        video_path (str): Path to the video file
        output_path (str): Path where the extracted frame will be saved
    """
    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False
    
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Check if video opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return False
    
    # Get total number of frames
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        print(f"Error: No frames found in the video file {video_path}")
        return False
    
    # Set the position to the last frame
    # Note: Setting to total_frames-1 as frame counting starts from 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    
    # Read the last frame
    ret, frame = cap.read()
    
    # Check if frame was successfully read
    if not ret:
        print("Error: Could not read the last frame")
        return False
    
    # Save the frame as an image
    cv2.imwrite(output_path, frame)
    print(f"Last frame successfully saved to {output_path}")
    
    # Release video capture object
    cap.release()
    
    return True

def generate_video(image_path, prompt):
    """Generate a video using Kling AI."""
    print(f"Generating video using Kling AI...")
    
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
    aspect_ratio = settings.get('aspect_ratio', '16:9')
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

def generate_music(prompt):
    """Generate music using Sonauto."""
    print(f"Generating music using Sonauto...")
    
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
    
    # Generate a unique filename
    timestamp = int(time.time())
    music_filename = f"music/sonauto_music_{timestamp}.mp3"
    
    # Prepare the request payload
    payload = {
        "prompt": prompt,
        "tags": ["country music", "female vocals", "acoustic guitar", "cowboy"],
        "instrumental": False,
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

def merge_videos(video_paths, music_path):
    """Merge videos with music using FFMPEG."""
    print(f"Creating final video by merging {len(video_paths)} videos with music...")
    
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
    
    # Now add music to the concatenated video
    ffmpeg_cmd = f'ffmpeg -y -i "{concat_output}" -i "{music_path}" -map 0:v -map 1:a -shortest -t 50 -c:v libx264 -c:a aac -b:a 192k "{output_filename}"'
    
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
        # Use an existing image from the images directory
        first_image_path = "image/music.png"  # Update this path to match your actual image
        
        # Create a default prompt for the video generation
        first_prompt = "music video, cinematic"
        
        print(f"Using existing image: {first_image_path}")
        
        # Step 1: Generate first video from the existing image
        first_video_path = generate_video(first_image_path, first_prompt)
        
        # Step 2: Extract the last frame from the first video
        second_image_path = f"image/last_frame_video1_{int(time.time())}.png"
        extract_last_frame(first_video_path, second_image_path)
        
        # Step 3: Generate second video from the last frame of the first video
        second_video_path = generate_video(second_image_path, first_prompt)
        
        # Step 4: Extract the last frame from the second video
        third_image_path = f"image/last_frame_video2_{int(time.time())}.png"
        extract_last_frame(second_video_path, third_image_path)
        
        # Step 5: Generate third video from the last frame of the second video
        third_video_path = generate_video(third_image_path, first_prompt)
        
        # Step 6: Extract the last frame from the third video
        fourth_image_path = f"image/last_frame_video3_{int(time.time())}.png"
        extract_last_frame(third_video_path, fourth_image_path)
        
        # Step 7: Generate fourth video from the last frame of the third video
        fourth_video_path = generate_video(fourth_image_path, first_prompt)
        
        # Step 8: Extract the last frame from the fourth video
        fifth_image_path = f"image/last_frame_video4_{int(time.time())}.png"
        extract_last_frame(fourth_video_path, fifth_image_path)
        
        # Step 9: Generate fifth video from the last frame of the fourth video
        fifth_video_path = generate_video(fifth_image_path, first_prompt)
        
        # Step 10: Generate music using a prompt
        music_prompt = "country music, female vocals, acoustic guitar, cowboy"
        music_path = generate_music(music_prompt)
        
        print(f"Using video files: {first_video_path}, {second_video_path}, {third_video_path}, {fourth_video_path}, {fifth_video_path}")
        print(f"Using music file: {music_path}")
        
        # Step 11: Merge videos with music
        video_paths = [first_video_path, second_video_path, third_video_path, fourth_video_path, fifth_video_path]
        final_video = merge_videos(video_paths, music_path)
        
        print("\nContent Generation Pipeline Complete!")
        print(f"Input Image: {first_image_path}")
        print(f"Generated Images: {second_image_path}, {third_image_path}, {fourth_image_path}, {fifth_image_path}")
        print(f"Generated Videos: {first_video_path}, {second_video_path}, {third_video_path}, {fourth_video_path}, {fifth_video_path}")
        print(f"Generated Music: {music_path}")
        print(f"Final Output: {final_video}")
        
    except Exception as e:
        print(f"Error in content generation pipeline: {str(e)}")
        print("Process failed. Please try running the script again.")

if __name__ == "__main__":
    main()
