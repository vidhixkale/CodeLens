# CodeLens - Local Code Reviewer (MCP)

Privacy-first local code review powered by a local LLM (Ollama) and a lightweight FastAPI backend with a Vite + React + Tailwind frontend.

## Prereqs
- Windows 10/11 (PowerShell)
- Python 3.11+
- Node.js 18+
- Ollama installed and running

## Project structure

```
code-reviewer-mcp/
	mcp_server/           # Backend (FastAPI)
		server.py
		tools.py
	frontend/             # Frontend (Vite + React + Tailwind)
		index.html
		package.json
		src/
			App.jsx
			main.jsx
			index.css
	.env                  # Backend env (OLLAMA_URL, OLLAMA_MODEL, HOST, PORT)
	frontend/
        .env         # Frontend env (VITE_API_URL)
	requirements.txt      # Backend Python deps
```

Note: The backend uses the underscored package `mcp_server` (not the hyphenated `mcp-server`).

## 1) Install Ollama
- Download: https://ollama.com
- Verify and pull model (in PowerShell):

```powershell
ollama --version
ollama pull llama3.1:8b
ollama run llama3.1:8b "Write a hello world in Python"
```

Ollama default API URL: http://localhost:11434

## 2) Configure env files

- Backend env at `code-reviewer-mcp/.env`:

```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
HOST=127.0.0.1
PORT=8000
```

- Frontend env at `code-reviewer-mcp/frontend/.env`:

```
VITE_API_URL=http://127.0.0.1:8000
```

The backend automatically loads `.env` via python-dotenv. The frontend reads `VITE_*` variables at build time via Vite.

## 3) Backend setup (FastAPI)
From the repo root `code-reviewer-mcp`:

```powershell
# (Optional) Create and activate venv
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the server (uses .env values by default)
uvicorn mcp_server.server:app --reload

# Alternatively, pass host/port explicitly
# uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000 --reload

# Or make uvicorn load the .env itself
# uvicorn mcp_server.server:app --reload --env-file .env
```

Health check:
```powershell
curl http://127.0.0.1:8000/health
```

## 4) Frontend setup (Vite + React + Tailwind)
From the repo root `code-reviewer-mcp`:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Sample output
![MCP Screenshot](./output/image.png)


## API
- POST /review { code, language } -> { review, timestamp, model }
- POST /read-file { file_path } -> { path, content }
- POST /list-directory { dir_path } -> { path, entries }
- GET /health -> status

## Troubleshooting
- ERROR: [Errno 11001] getaddrinfo failed
	- Cause: empty HOST/PORT in shell. Fix by omitting flags or setting them explicitly.
	- Example:
		```powershell
		uvicorn mcp_server.server:app --reload
		# or
		uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000 --reload
		```
- Frontend can’t reach API
	- Confirm backend is running at http://127.0.0.1:8000
	- Ensure `frontend/.env` has `VITE_API_URL=http://127.0.0.1:8000`
	- Restart `npm run dev` after changing `.env`

## Notes
- Reviews run locally via Ollama; no code leaves your machine.
- Example file: `examples/buggy_code.py` (copy/paste or use the Read by path feature).
- Tailwind is used for styling; highlight.js is used for code block highlighting in results.

## License
MIT
