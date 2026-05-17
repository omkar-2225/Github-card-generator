# GitHub Card Generator

A web application that generates beautiful, shareable cards for GitHub profiles. It consists of a Python backend and an HTML/JS/CSS frontend, and is fully containerized using Docker.

## Live Demo

- **Frontend**: [https://github-card-frontend-15131588805.us-central1.run.app](https://github-card-frontend-15131588805.us-central1.run.app)
- **Backend API**: [https://github-card-backend-15131588805.us-central1.run.app](https://github-card-backend-15131588805.us-central1.run.app)

*(Note: These services are currently deployed on Google Cloud Run)*

## Features

- **Profile Scraping**: Automatically fetches GitHub profile data (repos, followers, stars).
- **AI-Powered Analysis**: Uses Google's Gemini AI to analyze the profile and generate a unique persona/summary.
- **Card Generation**: Dynamically creates a beautiful, shareable image card customized to the user.
- **Agentic Fallback**: Built-in recovery mode ensures the app continues to function even if the primary AI agent hits a quota limit.
- **Model Selection**: Allows choosing different Gemini models (e.g., gemini-3.1-flash-lite) for generation.

## Tech Stack

- **Backend**: Python, FastAPI, Google Agentic Data Kit (ADK), Gemini API.
- **Frontend**: HTML, CSS, Vanilla JavaScript, Nginx.
- **Infrastructure**: Docker, Docker Compose, Google Cloud Run.

## Project Structure

- `/frontend` - Contains the HTML, CSS, and Nginx configuration for serving the static web interface.
- `/backend` - Contains the Python API (FastAPI) responsible for fetching GitHub data and generating the cards.

## Local Development

You can run the entire application locally using Docker Compose.

## Deployment (Google Cloud Run)

The application is designed to be easily deployable to Google Cloud Run as two separate services.
