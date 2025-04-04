# AI Prompt Templates

This directory contains prompt templates used by the AI Video Generator to create various elements of the video.

## Files

- `idea_gen.txt` - Prompt for generating creative video concepts using GPT-4o
- `idea_gen2.txt` - Alternative prompt for idea generation with different parameters
- `music_gen.txt` - Prompt for generating music using SonAuto
- `video_gen.txt` - Prompt for generating videos using Kling AI
- `voice_examples.txt` - Examples and parameters for voice generation using OpenAI TTS

## Usage

These prompt templates are used by the `services/video_generation.py` module to generate different components of the video. They are designed to produce consistent, high-quality outputs from the AI models.

## Customization

You can customize these prompts to change the style, tone, or content of the generated elements. For example:

- Modify `idea_gen.txt` to focus on specific themes or styles
- Adjust `music_gen.txt` to generate different genres of music
- Update `video_gen.txt` to change the visual style of generated videos

When modifying prompts, be careful to maintain the expected format that the code is looking for when parsing the AI responses.
