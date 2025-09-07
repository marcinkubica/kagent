from __future__ import annotations

import argparse
import asyncio
from typing import Dict, List

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message as TextualMessage
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Static, ListView, ListItem, Label
try:  # Textual >=0.59 provides TextArea
    from textual.widgets import TextArea  # type: ignore
except Exception:  # pragma: no cover
    TextArea = None  # fallback
try:  # Textual version differences
    from textual.screen import ModalScreen  # type: ignore
except Exception:  # pragma: no cover
    from textual.screens import ModalScreen  # type: ignore

from .backend import BackendClient, Agent, Message as ChatMessage


def pretty_agent_name(agent: Agent) -> str:
    name = agent.id or agent.name
    if "__NS__" in name:
        name = name.split("__NS__", 1)[1]
    if name.endswith("_agent"):
        name = name[:-6]
    return name.replace("_", "-")


class AgentList(ListView):
    class AgentSelected(TextualMessage):
        def __init__(self, agent: Agent) -> None:
            self.agent = agent
            super().__init__()

    def __init__(self, *, id: str | None = None):
        super().__init__(id=id)
        self._agents: List[Agent] = []

    async def set_agents(self, agents: List[Agent]):
        # Sort agents by human friendly name (case-insensitive)
        agents = sorted(agents, key=lambda a: pretty_agent_name(a).lower())
        self._agents = agents
        self.clear()
        for ag in agents:
            self.append(ListItem(Label(pretty_agent_name(ag))))
        if agents:
            self.index = 0
            # post_message returns a boolean (handled synchronously); don't await
            self.post_message(self.AgentSelected(agents[0]))

    async def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[override]
        idx = getattr(event, "index", None)
        if idx is None:
            idx = getattr(event, "item_index", None)  # compatibility with textual versions
        if isinstance(idx, int) and 0 <= idx < len(self._agents):
            self.post_message(self.AgentSelected(self._agents[idx]))

    def current_agent(self) -> Agent | None:
        if not self._agents:
            return None
        if self.index is None:
            return None
        if 0 <= self.index < len(self._agents):
            return self._agents[self.index]
        return None


class ChatView(Static):
    BINDINGS = [Binding("c", "clear", "Clear chat")]

    def __init__(self, id: str | None = None):
        super().__init__(id=id)
        self.lines: List[str] = []

    def add_message(self, msg: ChatMessage, append: bool = True):
        if msg.role == "assistant":
            # combine assistant tokens continuously
            if append and self.lines and self.lines[-1].startswith("assistant:"):
                self.lines[-1] += msg.content
            else:
                self.lines.append(f"assistant: {msg.content}")
        else:
            self.lines.append(f"{msg.role}: {msg.content}")
        self.update("\n".join(self.lines[-400:]))  # keep last 400 lines
        self.scroll_end(animate=False)

    def action_clear(self):
        self.lines.clear()
        self.update("")

    def show_sessions(self, agent: Agent, sessions):  # sessions: List[Dict]
        """Display sessions list for an agent.

        Each session dict may contain: id, name, created_at.
        """
        if not sessions:
            body = f"[b]{pretty_agent_name(agent)}[/b]\n(no sessions yet)"
        else:
            lines = []
            for sess in sessions:
                if isinstance(sess, dict):
                    sid = sess.get("id", "?")
                    short = sid[:8]
                    name = sess.get("name") or "-"
                    lines.append(f"• {name} ({short})")
                else:
                    lines.append(f"• {sess}")
            rendered = "\n".join(lines)
            body = f"[b]{pretty_agent_name(agent)} sessions[/b]\n{rendered}"
        self.update(body)

    def show_all_sessions(self, sessions):  # sessions: List[Dict]
        if not sessions:
            self.update("(no sessions)")
            return
        lines = ["[b]All sessions[/b]", "ID(short)  NAME         AGENT"]
        for sess in sessions[:200]:
            if not isinstance(sess, dict):
                continue
            sid = str(sess.get("id", ""))
            short = sid[:8]
            name = sess.get("name") or "-"
            agent_id = sess.get("agent_id") or ""
            lines.append(f"{short:<9} {name:<12} {agent_id}")
        self.update("\n".join(lines))


class InputBar(Horizontal):
    class Submitted(TextualMessage):
        def __init__(self, text: str):
            self.text = text
            super().__init__()

    def compose(self) -> ComposeResult:  # type: ignore[override]
        if TextArea is not None:
            editor = ChatEditor(id="chat-input")
        else:  # fallback to single-line Input
            editor = Input(placeholder="Type a message...", id="chat-input")
        yield editor
        yield Static("Ctrl+Enter: send | ?: help", id="hint")

    async def on_input_submitted(self, event: Input.Submitted):  # fallback path when TextArea missing
        text = event.value.strip()
        if text:
            self.post_message(self.Submitted(text))
            event.input.value = ""


class ChatEditor(TextArea if TextArea is not None else Static):  # type: ignore[misc]
    """Multi-line editor using TextArea; Ctrl+Enter sends, plain Enter inserts newline.

    Falls back to a read-only Static (should not happen unless TextArea import failed).
    """
    DEFAULT_TEXT = ""

    def __init__(self, *args, **kwargs):  # type: ignore[override]
        if TextArea is not None:
            super().__init__(*args, **kwargs)
            self.border_title = "prompt"
        else:  # pragma: no cover
            super(Static, self).__init__()  # type: ignore

    def key_enter(self) -> None:  # textual TextArea hook
        # Normal Enter => newline (TextArea default)
        if TextArea is not None:
            return super().key_enter()  # type: ignore

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        if event.key == "enter":
            mods = set(getattr(event, "modifiers", []) or [])
            if "ctrl" in mods or "meta" in mods:  # submit
                text = self.document.text.strip() if TextArea is not None else ""
                if text:
                    # Bubble submission
                    self.post_message(InputBar.Submitted(text))
                    if TextArea is not None:
                        self.load_text("")
                event.stop()
            else:
                # Let normal newline occur
                return
        


class StatusBar(Static):
    status = reactive("Ready")
    agent = reactive("-")
    session = reactive("-")

    def watch_status(self, value: str):  # type: ignore[override]
        self._refresh()

    def watch_agent(self, value: str):  # type: ignore[override]
        self._refresh()

    def watch_session(self, value: str):  # type: ignore[override]
        self._refresh()

    def _refresh(self):
        self.update(f"[b]{self.status}[/b] | Agent: {self.agent} | Session: {self.session}")


class HelpScreen(ModalScreen):  # type: ignore[type-arg]
    def compose(self) -> ComposeResult:  # type: ignore[override]
        help_text = """
        [b]kagentino Help[/b]\n
        [b]Navigation[/b]
        Up/Down or k/j  : Navigate agents
        Enter           : Select agent (when agent list focus)
        Ctrl+L          : Focus agent list
        Ctrl+K          : Focus chat

        [b]Chat Editing[/b]
        Ctrl+Enter      : Send message
        Enter           : New line

        [b]Misc[/b]
        Ctrl+C / q      : Quit
        ?               : Toggle this help
        c               : Clear chat
        / (planned)     : Command palette

        Press any key to close.
        """
        yield Static(help_text, id="help")

    def on_key(self, _: events.Key) -> None:  # type: ignore[override]
        self.app.pop_screen()


class KAgentinoApp(App):
    CSS = """
    Screen { layout: horizontal; background: $surface; }
    #left { width: 24%; min-width:28; border: panel $accent; }
    #chat { layout: vertical; border: panel $primary; }
    #chat-view { padding: 0 1; height: 1fr; }
    #input { dock: bottom; height:5; }
    #chat-input { width: 100%; height:100%; overflow: auto; border: panel $accent; }
    #spacer { height:1; }
    #status { dock: bottom; height:1; background: $accent-darken-3; color: $text; }
    #chat-input { width: 100%; }
    #hint { width: 100%; text-style: dim; }
    Static#help { padding: 1 2; border: panel $primary; background: $boost; }
    /* Hover highlight for agent list items */
    #agents ListItem:hover { background: $accent-darken-1; text-style: bold; }
    """
    # Title shown in the Header (otherwise Textual defaults to the class name)
    TITLE = "kagentino"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("tab", "focus_next", "Focus"),
        Binding("a", "focus_agents", "Agents"),
    Binding("s", "show_sessions", "Sessions"),
        Binding("f", "focus_input", "Input"),
        Binding("?", "toggle_help", "Help"),
    ]

    def __init__(self, backend: BackendClient):
        super().__init__()
        self.backend = backend
        self.current_agent: Agent | None = None
        self.session_ids: Dict[str, str] = {}
        self.streaming_task: asyncio.Task | None = None

    async def on_mount(self) -> None:  # type: ignore[override]
        self.call_later(self._load_agents)

    async def _load_agents(self):
        self.query_one(StatusBar).status = "Loading agents..."
        agents = await self.backend.list_agents()
        await self.query_one(AgentList).set_agents(agents)
        self.query_one(StatusBar).status = f"Loaded {len(agents)} agents"
        # Load all sessions to show initially
        try:
            sessions = await self.backend.list_all_sessions()
            self.query_one(ChatView).show_all_sessions(sessions)
        except Exception:  # pragma: no cover
            pass
        # Dynamically size the left pane width to fit the longest agent name with padding.
        try:
            if agents:
                longest = max(len(pretty_agent_name(a)) for a in agents)
                # Rough character cell to width mapping; add padding + borders.
                # Minimum width 20, maximum 60 columns to avoid overly wide sidebar.
                target_cols = min(60, max(20, longest + 6))  # +6 for padding, border, scroll bar space
                left_container = self.query_one('#left')
                # Apply an absolute width in columns (characters). Textual supports int assignment.
                left_container.styles.width = target_cols
                # Ensure min-width isn't larger than chosen width so shrink applies.
                left_container.styles.min_width = min(int(getattr(left_container.styles, 'min_width', 0) or 0), target_cols) or None
        except Exception:
            # Non-fatal; keep default if anything goes wrong.
            self.log("Could not auto-size left pane", level="warning")

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(name="kagentino")
        with Container(id="left"):
            yield AgentList(id="agents")
        with Container(id="chat"):
            yield ChatView(id="chat-view")
            yield InputBar(id="input")
            yield Static("", id="spacer")
            yield StatusBar(id="status")
        yield Footer()

    async def handle_agent_list_agent_selected(self, message: AgentList.AgentSelected):  # type: ignore[override]
        self.current_agent = message.agent
        sb = self.query_one(StatusBar)
        sb.status = "Agent selected"
        sb.agent = pretty_agent_name(message.agent)
        # No implicit session creation; will create on first message
        sb.session = "-"
        # Update input placeholder
        try:
            input_widget = self.query_one('#chat-input')  # type: ignore
            label = f"→ {pretty_agent_name(message.agent)}"
            if hasattr(input_widget, 'placeholder'):
                setattr(input_widget, 'placeholder', f"Message {label}")
            if hasattr(input_widget, 'border_title'):
                setattr(input_widget, 'border_title', label)
        except Exception:  # pragma: no cover
            pass
        # Show sessions list
        try:
            sessions = await self.backend.list_sessions(message.agent)
            self.query_one(ChatView).show_sessions(message.agent, sessions)
        except Exception:  # pragma: no cover
            pass

    async def on_list_view_highlighted(self, event: ListView.Highlighted):  # type: ignore[override]
        """When user hovers / moves cursor in agent list, show sessions for that agent."""
        try:
            agent_list = self.query_one(AgentList)
            agent = agent_list.current_agent()
            if not agent:
                return
            sessions = await self.backend.list_sessions(agent)
            self.query_one(ChatView).show_sessions(agent, sessions)
            sb = self.query_one(StatusBar)
            sb.status = "Agent focus"
            sb.agent = pretty_agent_name(agent)
        except Exception:  # pragma: no cover
            pass

    async def handle_input_bar_submitted(self, message: InputBar.Submitted):  # type: ignore[override]
        if not self.current_agent:
            self.query_one(StatusBar).status = "No agent selected"
            return
        # Ensure session exists (lazy creation)
        if self.current_agent.ref not in self.session_ids:
            sid = await self.backend.create_session(self.current_agent)
            self.session_ids[self.current_agent.ref] = sid
        session_id = self.session_ids[self.current_agent.ref]
        self.query_one(StatusBar).session = session_id[:8]
        # Cancel any existing streaming
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
        chat_view = self.query_one(ChatView)
        chat_view.add_message(ChatMessage(role="user", content=message.text))
        self.streaming_task = asyncio.create_task(self._do_stream(self.current_agent, session_id, message.text))

    async def _do_stream(self, agent: Agent, session_id: str, text: str):
        self.query_one(StatusBar).status = "Streaming..."
        try:
            async for msg in self.backend.stream_message(agent, session_id, text):
                # Break out if app no longer running (Textual provides is_running())
                if hasattr(self, 'is_running') and not self.is_running:
                    break
                if msg.role == "user":
                    continue  # already displayed
                self.query_one(ChatView).add_message(msg)
            self.query_one(StatusBar).status = "Done"
        except Exception as e:  # pragma: no cover - display path
            self.query_one(StatusBar).status = f"Error: {e}"  # noqa: TRY401

    async def on_unmount(self) -> None:  # type: ignore[override]
        await self.backend.close()

    # Actions
    def action_focus_input(self) -> None:
        try:
            editor = self.query_one('#chat-input')  # type: ignore
            editor.focus()  # type: ignore
        except Exception:  # pragma: no cover
            pass

    def action_focus_agents(self) -> None:
        self.query_one(AgentList).focus()

    async def action_show_sessions(self) -> None:  # type: ignore[override]
        try:
            sessions = await self.backend.list_all_sessions()
            self.query_one(ChatView).show_all_sessions(sessions)
            sb = self.query_one(StatusBar)
            sb.status = "All sessions"
            sb.agent = "*"
            sb.session = "-"
        except Exception:  # pragma: no cover
            pass

    def action_toggle_help(self) -> None:
        if self.screen_stack and isinstance(self.screen_stack[-1], HelpScreen):  # type: ignore[attr-defined]
            self.pop_screen()
        else:
            self.push_screen(HelpScreen())


def run():
    parser = argparse.ArgumentParser(description="KAgent Textual Client")
    parser.add_argument("--base-url", default="http://127.0.0.1:8083", help="Base URL of kagent controller")
    parser.add_argument("--namespace", default="default")
    args = parser.parse_args()
    backend = BackendClient(args.base_url, namespace=args.namespace)
    app = KAgentinoApp(backend)
    app.run()


if __name__ == "__main__":  # pragma: no cover
    run()
