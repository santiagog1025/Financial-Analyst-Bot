# Financial Analyst Bot - Docker Setup

This guide explains how to run the Financial Analyst Bot using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

1. **Clone the repository and navigate to the project directory**

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your API keys (especially GROQ_API_KEY).

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Streamlit Frontend: http://localhost:8501
   - FastAPI Backend: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Alternative Docker Commands

### Build the image manually
```bash
docker build -t financial-analyst-bot .
```

### Run the container manually
```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env financial-analyst-bot
```

## Development

### Stop the services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Rebuild after changes
```bash
docker-compose up --build
```

## Troubleshooting

1. **Port conflicts**: If ports 8000 or 8501 are already in use, modify the port mappings in `docker-compose.yml`

2. **Environment variables**: Make sure your `.env` file contains all required API keys

3. **Build issues**: Try cleaning Docker cache:
   ```bash
   docker system prune -a
   ```

## File Structure

- `Dockerfile`: Main Docker configuration
- `docker-compose.yml`: Multi-service orchestration
- `.dockerignore`: Files to exclude from Docker build
- `requirements.txt`: Python dependencies
- `.env.example`: Template for environment variables
