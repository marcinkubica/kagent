# kagentino Next Steps / Roadmap

This document tracks the planned follow‑up work to evolve the initial Textual TUI into a fully functional rich CLI for KAgent.

## 1. Replace Stubs with Real Backend Calls
- Implement real HTTP calls:
  - GET /api/agents → populate `AgentList`
  - POST /api/sessions { name, agentRef } → return session ID
  - (Optionally) GET /api/sessions?agent=<ref> to reuse existing sessions
- Error handling: surface failures in `StatusBar` with clear retry guidance.
- Add configurable auth (token / kube-port-forward) hook (design placeholder interface now).

## 2. Implement True A2A Streaming
- Endpoint: POST stream to /api/a2a/{namespace}/{name}
- Send JSON body matching Go `protocol.SendMessageParams` (message id, parts array with text part).
- Consume chunked / line-delimited JSON events; parse into incremental assistant tokens.
- Graceful cancel (user presses Esc or Ctrl+C while streaming) → abort request.
- Reconnect / retry logic for transient network errors.

## 3. Message Assembly & Rendering
- Accumulate partial assistant events into a single logical message (token merge already stubbed).
- Support markdown (use `rich.markdown`) with a toggle for raw text.
- Syntax highlight code blocks.

## 4. Session & History Persistence
- Local cache file (e.g. ~/.kagentino/sessions/<agent>/<session_id>.jsonl)
- On load: display last N messages, continue streaming seamlessly.
- Prune / rotate large histories.

## 5. Enhanced UI Layout
- Split panes: left (agents), top-right (chat), bottom-right (details / tools / memories panel).
- Add command palette (Ctrl+P) for actions: switch agent, new session, clear, export.
- Status bar fields: latency, agent ref, session id, connection state (● green / ● yellow / ● red).

## 6. Tool & Memory Integration (Phase 1)
- Read /api/tools and /api/memories → list available.
- Allow inserting a tool invocation template into input via key binding.

## 7. Configuration System
- Precedence: CLI flags > env vars > config file (~/.config/kagentino/config.toml).
- Keys: base_url, namespace, auth.token, theme, history.max_messages.

## 8. Packaging & Distribution
- Add `pyproject.toml` (hatch or setuptools) with console_scripts entry: `kagentino = kagentino.app:run`.
- Optional `--install-completion` (typer or argcomplete if adding a non-TUI mode).

## 9. Testing Strategy
- Backend: pytest + respx to mock HTTP endpoints.
- Streaming parser: feed synthetic chunked responses, assert token assembly.
- UI: textual Pilot tests for sending input and verifying rendered lines.
- Add GitHub Action (reuse repo CI patterns) for lint + tests.

## 10. Error & Retry Model
- Central error handler → maps exceptions to user messages.
- Exponential backoff for agent list & streaming re-subscribe.
- Distinguish fatal (auth, 404 agent) vs transient (timeout, 5xx).

## 11. Telemetry (Optional / Opt-In)
- Count sessions started, messages sent (anonymous). Config flag: telemetry.enabled.

## 12. Accessibility & Theming
- High-contrast theme variant.
- Configurable color palette via CSS fragment override.

## 13. Performance Considerations
- Cap in-memory message list; virtualized scroll if needed after 5k lines.
- Stream processing: parse and render incrementally without blocking event loop (ensure awaits on small sleeps are removed once real streaming lands).

## 14. Security Considerations
- Redact tokens from logs.
- Provide clear warning if connecting over plain HTTP to non-localhost.

## 15. Stretch Ideas
- Multi-agent tabbed sessions.
- Inline tool result panels (collapsible blocks).
- Slash commands (/new, /agent <name>, /export, /help).
- Export chat to markdown / JSON.

## Suggested Implementation Order
1. Real HTTP calls (#1)
2. Streaming implementation (#2)
3. Parser & rendering improvements (#3)
4. Session persistence (#4)
5. Packaging (#8)
6. Tests & CI (#9)
7. Tool/memory panel (#6)
8. Config + theming (#7, #12)
9. Error/retry polish (#10)
10. Stretch features (#15)

## Acceptance Criteria (Next Milestone)
- Launch connects to live server, lists actual agents (no stub).
- Sending a message streams real assistant output.
- Cancel in-progress stream works.
- Session reused (does not create a new one each message) unless user requests new.
- Basic markdown formatting.

---
(Generated roadmap – update as features land.)
