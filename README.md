# Flowise Stack — One Command Setup

## Prerequisites

- Podman (or Docker) & Compose
- API keys for your providers

## Quick Start

### 1. Create secrets file

```bash
cp .env.secrets.example .env.secrets
nano .env.secrets
```

Add your API keys (uncomment and fill in):

```
OPENAI_API_KEY=sk-your-key-here
OPENROUTER_API_KEY=sk-or-your-key-here
```

### 2. Configure admin account (optional)

Edit `.env` to set your admin email/password:

```
ADMIN_NAME=Qasim
ADMIN_EMAIL=qasimlo900@gmail.com
ADMIN_PASSWORD=your-secure-password
```

### 3. Start the stack

```bash
./up.sh
```

This will:
- Start the Flowise container
- Wait until it's healthy
- Create the admin user (skips setup screen)
- Create all API credentials from `.env.secrets`

### 4. Open the UI

- **Flowise**: http://localhost:3000

### Stop the stack

```bash
./down.sh            # Stop containers (data preserved)
./down.sh --clean    # Stop and remove all volumes (data deleted)
```

## File Structure

```
.
├── docker-compose.yml      # Container definition
├── .env                    # Stack config (port, admin user)
├── .env.secrets            # Your API keys (git-ignored)
├── .env.secrets.example    # Template for secrets
├── up.sh                   # Start everything
├── down.sh                 # Stop everything
└── README.md               # This file
```

## Supported Credentials

| Provider       | .env.secrets key        |
|----------------|-------------------------|
| OpenAI         | OPENAI_API_KEY          |
| OpenRouter     | OPENROUTER_API_KEY      |
| Anthropic      | ANTHROPIC_API_KEY       |
| Google GenAI   | GOOGLE_GENAI_API_KEY    |
| Cohere         | COHERE_API_KEY          |
| Tavily         | TAVILY_API_KEY          |
| Jina AI        | JINA_API_KEY            |
| Pinecone       | PINECONE_API_KEY        |
| HuggingFace    | HUGGINGFACE_API_KEY     |
| Qdrant         | QDRANT_API_KEY          |
| Azure OpenAI   | AZURE_OPENAI_API_KEY    |
| ElasticSearch  | ELASTIC_CLOUD_ID        |
| Chroma         | CHROMA_API_KEY          |

## Adding New Credentials

To add a provider not listed above:

1. Create one manually in the Flowise UI
2. Find the credentialName and fields:
   ```bash
   podman exec flowise sqlite3 /root/.flowise/database.sqlite \
     "SELECT credentialName FROM credential;"
   ```
3. Decrypt to see field names:
   ```bash
   ENC_KEY=$(podman exec flowise cat /root/.flowise/encryption.key)
   ENC=$(podman exec flowise sqlite3 /root/.flowise/database.sqlite \
     "SELECT encryptedData FROM credential WHERE credentialName='xxx' LIMIT 1;")
   podman exec flowise node -e "
     const c = require('/usr/local/lib/node_modules/flowise/node_modules/crypto-js');
     console.log(c.AES.decrypt('$ENC','$ENC_KEY').toString(c.enc.Utf8));
   "
   ```
4. Add to `up.sh` following the existing pattern
