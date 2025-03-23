# AI Video Generator Pipeline 

An automated pipeline that generates creative videos using multiple AI models. The pipeline creates unique ideas, converts them into images, videos, and adds AI-generated music and voice narration.

## Features

- Idea generation using GPT-4o
- Image generation using Flux Image Pro
- Video generation using Kling AI
- Music generation using SonAuto
- Voice narration using OpenAI TTS
- Automatic video composition with FFMPEG

## Prerequisites

- Python 3.8 or higher
- FFMPEG installed on your system
- API keys for:
  - OpenAI
  - Replicate
  - SonAuto

## Installation

1. Clone the repository:
```bash
git clone https://github.com/All-About-AI-YouTube/ai_video_pipeline.git
cd ai_video_pipeline
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:

OPENAI_API_KEY=your_openai_key
REPLICATE_API_KEY=your_replicate_key
SONAUTO_API_KEY=your_sonauto_key


## Usage

Run the main script:
```bash
python auto_video.py  # For version with voice narration
```

The generated files will be saved in the following directories:
- `image/` - Generated images
- `video/` - Generated videos
- `music/` - Generated music
- `voice/` - Generated voice narration (if using auto_video.py)

## Project Structure

- `auto_video.py` - Main script with voice narration
- `prompts/` - Contains prompt templates for AI generation
  - `idea_gen.txt` - Prompts for idea generation
  - `video_gen.txt` - Settings for video generation
  - `music_gen.txt` - Settings for music generation
