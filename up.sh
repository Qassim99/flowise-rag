#!/bin/bash
set -e

#############################################################
#  Flowise Stack — One Command Setup
#
#  1. Create secrets:  cp .env.secrets.example .env.secrets
#                      nano .env.secrets
#  2. Start stack:     ./up.sh
#  3. Start + rebuild: ./up.sh --build
#  4. Open UI:         http://localhost:3000
#############################################################

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Detect container runtime
if command -v podman &>/dev/null; then
  RUNTIME="podman"
  COMPOSE="podman compose"
elif command -v docker &>/dev/null; then
  RUNTIME="docker"
  COMPOSE="docker compose"
else
  echo "ERROR: Neither podman nor docker found"
  exit 1
fi

CONTAINER="flowise"
DB_PATH="/root/.flowise/database.sqlite"
CRYPTO_JS_PATH="/usr/local/lib/node_modules/flowise/node_modules/crypto-js"

# Load config
source "$DIR/.env"

# ─── Step 1: Check secrets file ───────────────────────────
if [ ! -f "$DIR/.env.secrets" ]; then
  echo "╔══════════════════════════════════════════╗"
  echo "║  First run! Creating .env.secrets        ║"
  echo "║  Edit it with your API keys, then        ║"
  echo "║  run ./up.sh again.                      ║"
  echo "╚══════════════════════════════════════════╝"
  cp "$DIR/.env.secrets.example" "$DIR/.env.secrets"
  echo ""
  echo "Created: $DIR/.env.secrets"
  exit 0
fi

source "$DIR/.env.secrets"

# ─── Step 2: Start containers ─────────────────────────────
echo "▶ Starting Flowise..."
if [ "$1" = "--build" ]; then
  $COMPOSE up -d --build
else
  $COMPOSE up -d
fi

# ─── Step 3: Wait for healthy ─────────────────────────────
echo "⏳ Waiting for Flowise to be ready..."
for i in $(seq 1 60); do
  STATUS=$($RUNTIME inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "starting")
  if [ "$STATUS" = "healthy" ]; then
    echo "✓ Flowise is healthy"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "⚠ Timeout waiting for Flowise. Continuing anyway..."
  fi
  sleep 2
done

# Small extra delay for DB init
sleep 3

# ─── Step 4: Auto-create admin user (if needed) ──────────
USER_COUNT=$($RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM user;" 2>/dev/null || echo "0")

if [ "$USER_COUNT" = "0" ]; then
  echo ""
  echo "▶ Creating admin user..."

  # Generate bcrypt hash inside the container using node
  HASHED=$($RUNTIME exec "$CONTAINER" node -e "
    const bcrypt = require('bcryptjs');
    const hash = bcrypt.hashSync('$ADMIN_PASSWORD', 10);
    process.stdout.write(hash);
  " 2>/dev/null)

  if [ -z "$HASHED" ]; then
    echo "⚠ Could not hash password (bcryptjs not found). Skipping user creation."
    echo "  You'll need to create the admin account via the UI."
  else
    USER_UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')
    ORG_UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')
    WORKSPACE_UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')

    $RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" "
      INSERT INTO user (id, name, email, credential, tempToken, tokenExpiry, status, createdDate, updatedDate, createdBy, updatedBy)
      VALUES ('$USER_UUID', '$ADMIN_NAME', '$ADMIN_EMAIL', '$HASHED', NULL, datetime('now'), 'active', datetime('now'), datetime('now'), '$USER_UUID', '$USER_UUID');

      INSERT INTO organization (id, name, customerId, subscriptionId, createdDate, updatedDate, createdBy, updatedBy)
      VALUES ('$ORG_UUID', 'Default Organization', NULL, NULL, datetime('now'), datetime('now'), '$USER_UUID', '$USER_UUID');

      INSERT INTO workspace (id, name, description, createdDate, updatedDate, organizationId, createdBy, updatedBy)
      VALUES ('$WORKSPACE_UUID', 'Default Workspace', NULL, datetime('now'), datetime('now'), '$ORG_UUID', '$USER_UUID', '$USER_UUID');

      INSERT INTO organization_user (organizationId, userId, roleId, status, createdDate, updatedDate, createdBy, updatedBy)
      VALUES ('$ORG_UUID', '$USER_UUID', (SELECT id FROM role WHERE name = 'owner' LIMIT 1), 'active', datetime('now'), datetime('now'), '$USER_UUID', '$USER_UUID');

      INSERT INTO workspace_user (workspaceId, userId, roleId, status, lastLogin, createdDate, updatedDate, createdBy, updatedBy)
      VALUES ('$WORKSPACE_UUID', '$USER_UUID', (SELECT id FROM role WHERE name = 'owner' LIMIT 1), 'active', datetime('now'), datetime('now'), datetime('now'), '$USER_UUID', '$USER_UUID');
    "
    echo "✓ Admin user created: $ADMIN_EMAIL"
  fi
else
  echo "✓ Admin user already exists ($USER_COUNT users found)"
fi

# ─── Step 5: Auto-create credentials ─────────────────────
echo ""
echo "▶ Setting up API credentials..."

ENC_KEY=$($RUNTIME exec "$CONTAINER" printenv FLOWISE_SECRETKEY_OVERWRITE 2>/dev/null)
if [ -z "$ENC_KEY" ]; then
  ENC_KEY=$($RUNTIME exec "$CONTAINER" cat /root/.flowise/encryption.key 2>/dev/null)
fi

WORKSPACE_ID=$($RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" "SELECT id FROM workspace LIMIT 1;")

# Encrypt helper
encrypt() {
  $RUNTIME exec "$CONTAINER" node -e "
    const c = require('$CRYPTO_JS_PATH');
    process.stdout.write(c.AES.encrypt('$1', '$ENC_KEY').toString());
  "
}

# Create credential helper
create_cred() {
  local name="$1" credName="$2" jsonData="$3"
  local enc=$(encrypt "$jsonData")
  if [ -z "$enc" ]; then
    echo "  FAIL: $name (encryption error)"
    return
  fi
  local exists=$($RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM credential WHERE name='$name' AND credentialName='$credName';")
  if [ "$exists" -gt 0 ]; then
    $RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" \
      "UPDATE credential SET encryptedData='$enc', updatedDate=datetime('now')
       WHERE name='$name' AND credentialName='$credName';"
    echo "  ✓ $name ($credName) [updated]"
    return
  fi
  local uuid=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')
  $RUNTIME exec "$CONTAINER" sqlite3 "$DB_PATH" \
    "INSERT INTO credential (id, name, credentialName, encryptedData, createdDate, updatedDate, workspaceId)
     VALUES ('$uuid', '$name', '$credName', '$enc', datetime('now'), datetime('now'), '$WORKSPACE_ID');"
  echo "  ✓ $name ($credName) [created]"
}

# ── Create each credential if key exists ──
[ -n "$OPENAI_API_KEY" ]      && create_cred "OpenAI"       "openAIApi"           "{\"openAIApiKey\":\"$OPENAI_API_KEY\"}"
[ -n "$OPENROUTER_API_KEY" ]  && create_cred "OpenRouter"   "openRouterApi"       "{\"openRouterApiKey\":\"$OPENROUTER_API_KEY\"}"
[ -n "$ANTHROPIC_API_KEY" ]   && create_cred "Anthropic"    "chatAnthropicApi"    "{\"anthropicApiKey\":\"$ANTHROPIC_API_KEY\"}"
[ -n "$GOOGLE_GENAI_API_KEY" ] && create_cred "Google GenAI" "googleGenerativeAI" "{\"googleGenerativeAPIKey\":\"$GOOGLE_GENAI_API_KEY\"}"
[ -n "$COHERE_API_KEY" ]      && create_cred "Cohere"       "cohereApi"           "{\"cohereApiKey\":\"$COHERE_API_KEY\"}"
[ -n "$TAVILY_API_KEY" ]      && create_cred "Tavily"       "tavilyApi"           "{\"tavilyApiKey\":\"$TAVILY_API_KEY\"}"
[ -n "$JINA_API_KEY" ]        && create_cred "Jina AI"      "jinaAIApi"           "{\"jinaAIAPIKey\":\"$JINA_API_KEY\"}"
[ -n "$PINECONE_API_KEY" ]    && create_cred "Pinecone"     "pineconeApi"         "{\"pineconeApiKey\":\"$PINECONE_API_KEY\"}"
[ -n "$HUGGINGFACE_API_KEY" ] && create_cred "HuggingFace"  "huggingFaceApi"      "{\"huggingFaceApiKey\":\"$HUGGINGFACE_API_KEY\"}"
[ -n "$QDRANT_API_KEY" ]      && create_cred "Qdrant"       "qdrantApi"           "{\"qdrantApiKey\":\"$QDRANT_API_KEY\"}"

[ -n "$AZURE_OPENAI_API_KEY" ] && create_cred "Azure OpenAI" "azureOpenAIApi" \
  "{\"azureOpenAIApiKey\":\"$AZURE_OPENAI_API_KEY\",\"azureOpenAIApiInstanceName\":\"${AZURE_OPENAI_INSTANCE_NAME:-}\",\"azureOpenAIApiDeploymentName\":\"${AZURE_OPENAI_DEPLOYMENT_NAME:-}\",\"azureOpenAIApiVersion\":\"${AZURE_OPENAI_API_VERSION:-2024-02-15-preview}\"}"

[ -n "$ELASTIC_CLOUD_ID" ] && create_cred "ElasticSearch" "elasticSearchUserPassword" \
  "{\"cloudId\":\"$ELASTIC_CLOUD_ID\",\"username\":\"${ELASTIC_USERNAME:-elastic}\",\"password\":\"${ELASTIC_PASSWORD:-}\"}"

[ -n "$CHROMA_API_KEY" ] && create_cred "Chroma" "chromaApi" \
  "{\"chromaApiKey\":\"$CHROMA_API_KEY\",\"chromaTenant\":\"${CHROMA_TENANT:-default_tenant}\",\"chromaDatabase\":\"${CHROMA_DATABASE:-default_database}\"}"

# ─── Done ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✓ Flowise is ready!                     ║"
echo "║                                          ║"
echo "║  UI:    http://localhost:${PORT:-3000}             ║"
echo "║  Login: $ADMIN_EMAIL"
echo "╚══════════════════════════════════════════╝"
