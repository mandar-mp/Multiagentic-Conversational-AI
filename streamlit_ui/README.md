# Gemini-style Streamlit Chat UI

A lightweight Streamlit chatbot interface designed to connect to the FastAPI backend in this repo.

## Features

- Simple, modern chat UI inspired by Gemini.
- Backend integration using `POST /api/v1/chat`.
- Session-state chat history.
- Sidebar configuration and reset controls.
- Easy to customize with Streamlit layout and CSS.

## Run locally

1. Install dependencies:

```bash
python -m pip install -r streamlit_ui/requirements.txt
```

2. Start your backend API server (default `http://localhost:8000`).

3. Run Streamlit:

```bash
streamlit run streamlit_ui/app.py
```

## Configuration

- `CHAT_API_URL` environment variable can be used to point the UI to a different backend.
- The sidebar also exposes the backend API URL at runtime.

## Production deployment

The `streamlit_ui/Dockerfile` makes this UI production-ready with a minimal container.
