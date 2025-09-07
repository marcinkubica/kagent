from __future__ import annotations

import asyncio
import json
import os
import random
import string
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional, Dict, Any

import httpx


@dataclass
class Agent:
    id: str  # canonical ID (namespace/name hash or internal)
    namespace: str
    name: str
    title: str | None = None

    @property
    def ref(self) -> str:
        return f"{self.namespace}/{self.name}"


@dataclass
class Message:
    role: str  # user|assistant|system
    content: str
    ts: float = field(default_factory=lambda: time.time())


class BackendError(RuntimeError):
    pass


class BackendClient:
    """Thin abstraction over KAgent HTTP + A2A streaming.

    NOTE: This initial version stubs network calls with placeholder data if the
    endpoints are unreachable to allow UI development offline.
    """

    base_url: str
    namespace: str
    _http: httpx.AsyncClient
    # No local session store; sessions are managed by server

    def __init__(self, base_url: str, namespace: str = "default", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.namespace = namespace
        self._http = httpx.AsyncClient(timeout=timeout)
    # No in-memory sessions

    async def list_agents(self) -> List[Agent]:
        try:
            resp = await self._http.get(f"{self.base_url}/api/agents")
            if resp.status_code != 200:
                raise BackendError(f"agents list status={resp.status_code}")
            data = resp.json().get("data") or []
            agents: List[Agent] = []
            for item in data:
                # Expect item fields: id, namespace, name (guessing based on Go code)
                agent_id = item.get("id") or item.get("ID")
                ns = item.get("namespace") or item.get("Namespace") or self.namespace
                name = item.get("name") or item.get("Name") or agent_id.split("/")[-1]
                agents.append(Agent(id=agent_id, namespace=ns, name=name, title=item.get("title")))
            if agents:
                return agents
        except Exception:
            # fall back to stub
            pass
        # Offline stub
        return [
            Agent(id="default/echo", namespace="default", name="echo", title="Echo Agent"),
            Agent(id="default/helper", namespace="default", name="helper", title="Helper Agent"),
        ]

    async def create_session(self, agent: Agent, name: Optional[str] = None) -> str:
        """Create a session for an agent via HTTP.

        POST /api/sessions with JSON { name?, agent_ref }
        Returns session id or raises BackendError.
        """
        payload: Dict[str, Any] = {"agent_ref": agent.ref}
        if name:
            payload["name"] = name
        try:
            resp = await self._http.post(f"{self.base_url}/api/sessions", json=payload)
            if resp.status_code not in (200, 201):
                raise BackendError(f"create_session status={resp.status_code}")
            data = resp.json()
            session = data.get("data") or data.get("session") or data
            # session may be nested (api.NewResponse) => data is object
            sid = session.get("id") if isinstance(session, dict) else None
            if not sid:
                raise BackendError("missing session id in response")
            return sid
        except Exception as e:  # fallback offline stub
            # Offline stub: just generate ephemeral id
            return self._rand_id("sess")

    async def list_sessions(self, agent: Agent) -> List[Dict[str, Any]]:
        """List sessions for a specific agent via HTTP.

        GET /api/sessions/agent/{namespace}/{name}
        Returns list of sessions (dicts). On failure returns empty list.
        """
        try:
            url = f"{self.base_url}/api/sessions/agent/{agent.namespace}/{agent.name}"
            resp = await self._http.get(url)
            if resp.status_code != 200:
                raise BackendError(f"list_sessions status={resp.status_code}")
            body = resp.json()
            sessions = body.get("data") or []
            # Expect list of objects with id, name, created_at
            valid: List[Dict[str, Any]] = []
            for item in sessions:
                if not isinstance(item, dict):
                    continue
                if "id" in item:
                    valid.append(item)
            # Sort newest first by created_at if available
            valid.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            return valid
        except Exception:
            return []

    async def list_all_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions (GET /api/sessions). Returns list of session dicts."""
        try:
            resp = await self._http.get(f"{self.base_url}/api/sessions")
            if resp.status_code != 200:
                raise BackendError(f"list_all_sessions status={resp.status_code}")
            body = resp.json()
            sessions = body.get("data") or []
            if not isinstance(sessions, list):
                return []
            # Sort newest first
            def _created_at(item: Any) -> str:
                if isinstance(item, dict):
                    val = item.get("created_at")
                    return str(val) if val is not None else ""
                return ""
            sessions.sort(key=_created_at, reverse=True)
            return sessions
        except Exception:
            return []

    async def stream_message(self, agent: Agent, session_id: str, text: str) -> AsyncIterator[Message]:
        """Stream assistant response.

        Placeholder: yields a synthetic tokenized echo with small delay.
        Replace with real streaming from A2A endpoint:
        POST/stream to {base}/api/a2a/{agent.ref} with JSON body matching protocol
        and iterate over chunked lines -> parse JSON -> accumulate text parts.
        """
        # Emit user message first (for local echo)
        yield Message(role="user", content=text)
        # Fake assistant streaming tokens
        for token in self._fake_tokens(text):
            await asyncio.sleep(0.05)
            yield Message(role="assistant", content=token)

    def _fake_tokens(self, text: str):
        reply = f"You said: {text}. (demo stub)"
        for ch in reply:
            yield ch

    def _rand_id(self, prefix: str) -> str:
        return prefix + "-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

    async def close(self):
        await self._http.aclose()


__all__ = ["BackendClient", "Agent", "Message", "BackendError"]
