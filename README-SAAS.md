# AI Video Generator SaaS

A Software as a Service (SaaS) platform that generates creative videos using multiple AI models. The platform creates unique ideas, converts them into images, videos, and adds AI-generated music and voice narration.

## Features

- User authentication and account management
- Project creation and management
- Idea generation using GPT-4o
- Image generation using Flux Image Pro
- Video generation using Kling AI
- Music generation using SonAuto
- Voice narration using OpenAI TTS
- Automatic video composition with FFMPEG
- Background processing with Celery
- Subscription tiers with different capabilities

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Celery
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Redis, Celery
- **Containerization**: Docker, Docker Compose
- **AI Services**: OpenAI, Replicate, SonAuto

## Prerequisites

- Docker and Docker Compose
- API keys for:
  - OpenAI
  - Replicate
  - SonAuto

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai_video_saas.git
cd ai_video_saas
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit the `.env` file and add your API keys:
```
OPENAI_API_KEY=your_openai_key
REPLICATE_API_KEY=your_replicate_key
SONAUTO_API_KEY=your_sonauto_key
FLASK_SECRET_KEY=your_secret_key
```

4. Build and start the Docker containers:
```bash
docker-compose up -d
```

5. Access the application at http://localhost:5000

## Development

### Running without Docker

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install required packages:
```bash
pip install -r requirements-web.txt
```

3. Set up environment variables:
```bash
export FLASK_APP=app.py
export FLASK_DEBUG=1
```

4. Run the Flask application:
```bash
flask run
```

5. In a separate terminal, start Redis:
```bash
redis-server
```

6. In another terminal, start the Celery worker:
```bash
celery -A tasks.celery worker --loglevel=info
```

## Project Structure

- `app.py` - Main Flask application
- `tasks.py` - Celery tasks for background processing
- `services/` - Service modules for video generation
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JS, images)
- `prompts/` - Prompt templates for AI generation

## Deployment

For production deployment, consider the following:

1. Use a production-ready database like PostgreSQL
2. Set up proper SSL/TLS certificates
3. Configure a reverse proxy (Nginx, Apache)
4. Set up monitoring and logging
5. Use a managed Redis service for Celery
6. Configure proper storage for generated media files

## License

This project is licensed under the MIT License - see the LICENSE file for details.
