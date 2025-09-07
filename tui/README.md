# kagentui

Textual-based rich TUI for interacting with kagent agents over the A2A protocol.

## Goals (initial cut)
- Browse agents
- Create/select session per agent
- Send user messages
- Stream assistant responses (placeholder parsing of JSON events)
- Basic status bar (profile, namespace, latency)

## Status
MVP stub: backend client is minimal; extend to call actual REST + A2A streaming.

## Quick Start
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m kagentino.app --base-url http://127.0.0.1:8083 --namespace kagent
```

## Keybindings
- Up/Down: Navigate agent list / history
- Enter: Send message (focus in input)
- Ctrl+C / q: Quit
- Tab: Cycle focus

## Architecture
```
App (TextualApp)
 ├─ AgentList (ListView)
 ├─ ChatView (Static, scrollable, renders messages)
 ├─ InputBar (Input + send button)
 └─ StatusBar (Footer)
BackendClient (abstract HTTP + streaming A2A)
```

### Backend
Implements minimal list_agents(), create_session(agent_ref, name), stream_message(session_id, agent_ref, text). Streaming currently expects line-delimited JSON events (to be aligned with Go A2A MarshalJSON output).

## Next Steps
- Real HTTP calls to /api/agents, /api/sessions
- A2A streaming via websockets or HTTP chunked (match server protocol)
- Persist session history locally
- Theming & markdown rendering
- Tool / memory panels

## License
Apache-2.0 (inherits repository license)
