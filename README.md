# Flowise Stack — One Command Setup

## Prerequisites

- Podman (or Docker) & Compose
- API keys for your providers

## Quick Start

### 1. Create config file

```bash
cp .env.example .env
nano .env
```

Edit `.env` to set your admin account and API keys:

```
ADMIN_NAME=Qasim
ADMIN_EMAIL=qasimlo900@gmail.com
ADMIN_PASSWORD=Helloworld1$

OPENROUTER_API_KEY=sk-or-your-key-here
# TAVILY_API_KEY=tvly-your-key
```

### 2. Start the stack

```bash
./up.sh
```

This will:
- Start the Flowise container
- Wait until it's healthy
- Create all API credentials from `.env`

### 3. Open the UI

- **Flowise**: http://localhost:3000

### Stop the stack

```bash
./down.sh            # Stop containers (data preserved)
./down.sh --clean    # Stop and remove all volumes (data deleted)
```

## File Structure

```
 .
├──  chatbot-demo           # Embedded chatbot demo (served on :8080)
│   ├──  home.html          # Page with Flowise embed widget for testing
│   └──  web.js             # flowise-embed library for testing
├──  data                   # Persistent data for Flowise (Workflows, logs, etc.)
│   ├──  database.sqlite
│   ├──  encryption.key
│   ├──  logs
│   └──  storage
├──  docker-compose.yml     # Flowise + Qdrant + chatbot-demo services
├──  Dockerfile
├──  down.sh               # Stop everything
├──  qdrant_data           # Persistent data for Qdrant vector database
│   ├──  aliases
│   ├──  collections
│   └──  raft_state.json
├── 󰂺 README.md
└──  up.sh                 # Start everything      
```

## Supported Credentials

| Provider                | .env key           |
|-------------------------|--------------------|
| OpenAI (via OpenRouter) | OPENROUTER_API_KEY |
| OpenRouter              | OPENROUTER_API_KEY |
| Tavily                  | TAVILY_API_KEY     |
