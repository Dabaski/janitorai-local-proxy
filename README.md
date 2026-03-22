# JanitorAI Local LLM Proxy

Run local LLMs (via LM Studio) with JanitorAI using nginx reverse proxy and a CSP bypass browser extension.

## Overview

JanitorAI blocks custom API endpoints via Content Security Policy (CSP). This setup bypasses that restriction using:

1. **LM Studio** - Local LLM server (OpenAI-compatible API)
2. **nginx** - Reverse proxy that rewrites endpoints and handles CORS
3. **ngrok** - Exposes local server to the internet
4. **CSP Bypass Extension** - Firefox extension that removes CSP restrictions

```
JanitorAI → ngrok → nginx:5001 → LM Studio:1234
                      ↓
              Rewrites /chat/completions
                 to /v1/chat/completions
```

## Requirements

- Windows 10/11
- [LM Studio](https://lmstudio.ai/) 0.4.6+
- [ngrok](https://ngrok.com/) (free account)
- Firefox 109+ or Chrome/Brave
- A local LLM model (e.g., Qwen 3.5 9B, Llama, Mistral)

## Quick Start

### 1. Install & Configure LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Qwen 3.5 9B)
3. Load the model
4. **Important:** Disable "Thinking Mode" if using Qwen 3.x models
5. Start the local server (default port: 1234)

### 2. Install nginx

```bash
# Download nginx for Windows
curl -L -o nginx.zip https://nginx.org/download/nginx-1.24.0.zip

# Extract to C:\nginx-1.24.0
unzip nginx.zip -d C:\
```

### 3. Configure nginx

Replace `C:\nginx-1.24.0\conf\nginx.conf` with:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/json;

    sendfile        on;
    keepalive_timeout  65;

    upstream lmstudio {
        server 127.0.0.1:1234;
    }

    server {
        listen       5001;
        server_name  localhost;

        # Hide upstream CORS headers to avoid duplicates
        proxy_hide_header 'Access-Control-Allow-Origin';
        proxy_hide_header 'Access-Control-Allow-Methods';
        proxy_hide_header 'Access-Control-Allow-Headers';

        # JanitorAI sends to /chat/completions - proxy to /v1/chat/completions
        location = /chat/completions {
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
                add_header 'Access-Control-Max-Age' 86400;
                return 204;
            }

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

            proxy_pass http://lmstudio/v1/chat/completions;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header Content-Type $content_type;
            proxy_set_header Authorization $http_authorization;
            proxy_buffering off;
            proxy_read_timeout 300;
        }

        # Handle /models without /v1
        location = /models {
            add_header 'Access-Control-Allow-Origin' '*' always;
            proxy_pass http://lmstudio/v1/models;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        # Default - pass through as-is
        location / {
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '*';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
                add_header 'Access-Control-Max-Age' 86400;
                return 204;
            }

            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

            proxy_pass http://lmstudio;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_buffering off;
            proxy_cache off;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
            proxy_read_timeout 300;
        }
    }
}
```

### 4. Start nginx

```bash
cd C:\nginx-1.24.0
nginx.exe
```

### 5. Install ngrok

1. Download [ngrok](https://ngrok.com/download)
2. Create a free account and get your auth token
3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

### 6. Start ngrok

```bash
ngrok http 5001
```

Copy the public URL (e.g., `https://xxxx-xx-xx-xx-xx.ngrok-free.app`)

### 7. Install CSP Bypass Extension

**Firefox:**
1. Go to `about:debugging`
2. Click "This Firefox"
3. Click "Load Temporary Add-on..."
4. Select `csp-bypass-extension/manifest.json`

**Chrome/Brave:**
1. Go to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `csp-bypass-extension` folder

### 8. Configure JanitorAI

1. Go to JanitorAI
2. Open API Settings
3. Select "Proxy" or "OpenAI Compatible"
4. Enter:
   - **API URL:** `https://your-ngrok-url.ngrok-free.app` (no /v1)
   - **API Key:** Any value (e.g., `sk-local`)
   - **Model:** `qwen/qwen3.5-9b` (or your model name)

## Troubleshooting

### "Thinking Process:" in responses
- Disable thinking mode in LM Studio model settings
- Reload the model after changing settings

### CORS errors
- Make sure nginx is running (not the Python proxy)
- Check only ONE process is on port 5001: `netstat -ano | grep 5001`

### "Unexpected endpoint" errors
- nginx rewrites `/chat/completions` to `/v1/chat/completions`
- Use base URL without `/v1` in JanitorAI

### CSP still blocking
- Verify the extension is installed and enabled
- Check the extension icon shows "Enabled"
- Try refreshing JanitorAI page

### ngrok URL changed
- Free tier URLs change on restart
- Check `http://localhost:4040` for current URL
- Consider Cloudflare Tunnel for permanent URLs

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  JanitorAI  │────▶│    ngrok    │────▶│    nginx    │────▶│  LM Studio  │
│  (Browser)  │     │   :443      │     │   :5001     │     │   :1234     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │                                       ▼
       │                              ┌─────────────────┐
       │                              │ Path Rewriting  │
       │                              │ /chat/completions│
       │                              │       ↓         │
       │                              │/v1/chat/completions│
       │                              └─────────────────┘
       ▼
┌─────────────────┐
│  CSP Bypass     │
│  Extension      │
│  (Removes CSP)  │
└─────────────────┘
```

## Files

```
JanitorAI Proxy/
├── README.md                 # This file
├── config.txt                # Quick reference config
├── csp-bypass-extension/     # Firefox/Chrome extension
│   ├── manifest.json
│   ├── background.js
│   ├── popup/
│   ├── options/
│   ├── icons/
│   └── tests/
├── ngrok.exe                 # ngrok binary
├── proxy_server.py           # Alternative Python proxy (not needed)
├── test_connection.py        # Connection test script
├── test_page.html            # Browser test page
└── SillyTavern/              # Alternative frontend (optional)
```

## Alternative: SillyTavern

If you prefer not to use JanitorAI, [SillyTavern](https://github.com/SillyTavern/SillyTavern) works directly with LM Studio without needing ngrok or CSP bypass:

```bash
cd SillyTavern
npm install
node server.js
```

Then open `http://localhost:8000` and configure:
- API: Chat Completion > Custom (OpenAI-compatible)
- Endpoint: `http://localhost:1234/v1`
- Model: `qwen/qwen3.5-9b`

## License

MIT

## Credits

- [LM Studio](https://lmstudio.ai/) - Local LLM runtime
- [nginx](https://nginx.org/) - Reverse proxy
- [ngrok](https://ngrok.com/) - Tunneling service
