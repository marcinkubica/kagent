import asyncio
import pytest

from src.backend import BackendClient, Agent


@pytest.mark.asyncio
async def test_fake_streaming():
    client = BackendClient("http://invalid-host")
    agents = await client.list_agents()
    assert agents, "Should get stub agents offline"
    agent = agents[0]
    session = await client.create_session(agent)
    # listing may fail offline; ensure it returns a list
    sessions = await client.list_sessions(agent)
    assert isinstance(sessions, list)
    chunks = []
    async for msg in client.stream_message(agent, session, "hello"):
        if msg.role == "assistant":
            chunks.append(msg.content)
    # ensure some assistant output aggregated
    assert any(chunks), "Expected assistant chunks"
    await client.close()
