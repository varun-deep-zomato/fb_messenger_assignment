import pytest
import httpx
from datetime import datetime
import logging

from cassandra.cqltypes import EMPTY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from hashlib import sha256
import uuid

def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    sorted_ids = sorted([user1_id, user2_id])
    hash_input = (sorted_ids[0] + sorted_ids[1]).encode()
    return str(uuid.UUID(sha256(hash_input).hexdigest()[0:32]))

API_BASE = "http://localhost:6969/api"

USERS = [
    {"user_id": "11111111-1111-1111-1111-111111111111", "username": "alice"},
    {"user_id": "22222222-2222-2222-2222-222222222222", "username": "bob"},
    {"user_id": "33333333-3333-3333-3333-333333333333", "username": "carol"},
    {"user_id": "44444444-4444-4444-4444-444444444444", "username": "dave"},
]

# Conversation IDs generated via util.generate_conversation_id
CONV_USER1_USER2 = generate_conversation_id(USERS[0]["user_id"], USERS[1]["user_id"])
CONV_USER1_USER3 = generate_conversation_id(USERS[0]["user_id"], USERS[2]["user_id"])
EMPTYID = str(uuid.UUID(int=0))
CONV_USER2_USER3 = generate_conversation_id(USERS[1]["user_id"], USERS[2]["user_id"])
CONV_USER3_USER1 = generate_conversation_id(USERS[2]["user_id"], USERS[0]["user_id"])

from hashlib import sha256
import uuid

def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    sorted_ids = sorted([user1_id, user2_id])
    hash_input = (sorted_ids[0] + sorted_ids[1]).encode()
    return str(uuid.UUID(sha256(hash_input).hexdigest()[0:32]))

@pytest.mark.asyncio
async def test_user_with_no_conversations():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/conversations/user/{USERS[3]['user_id']}")
        logger.info(f"[test_user_with_no_conversations] Response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []

@pytest.mark.asyncio
async def test_empty_conversation():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/messages/conversation/{EMPTYID}")
        logger.info(f"[test_empty_conversation] Response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []

@pytest.mark.asyncio
async def test_single_message_conversation():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/messages/conversation/{CONV_USER2_USER3}")
        logger.info(f"[test_single_message_conversation] Response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["content"] == "Yo Carol!"
        assert data["data"][0]["sender_id"] == USERS[1]["user_id"]
        assert data["data"][0]["receiver_id"] == USERS[2]["user_id"]

@pytest.mark.asyncio
async def test_paginated_conversation():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/messages/conversation/{CONV_USER1_USER2}?limit=20")
        logger.info(f"[test_paginated_conversation] First page response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 20
        assert data["limit"] == 20
        assert data["next_cursor"] is not None
        next_cursor = data["next_cursor"]
        resp2 = await client.get(f"{API_BASE}/messages/conversation/{CONV_USER1_USER2}?limit=20&before_message_id={next_cursor}")
        logger.info(f"[test_paginated_conversation] Second page response: {resp2.json()}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        # Will only work once the test is run cause the second time the count will increase by 1 because of other tests writing to the same conversation
        assert data2["total"] == 8
        assert data2["next_cursor"] is None or data2["next_cursor"]
        all_msgs = data["data"] + data2["data"]
        contents = [msg["content"] for msg in all_msgs]
        assert contents[0] == "Paginated message 25"
        assert contents[-1] == "Hey Bob!"

@pytest.mark.asyncio
async def test_special_and_edge_content_messages():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE}/messages/conversation/{CONV_USER3_USER1}")
        logger.info(f"[test_special_and_edge_content_messages] Response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        contents = [msg["content"] for msg in data["data"]]
        assert "" in contents  # empty content
        assert any("!@#$%^&*()_+|~`" in c for c in contents)
        assert any(len(c) == 1000 for c in contents)
        assert contents.count("Same timestamp") == 1
        assert contents.count("Same timestamp again") == 1

@pytest.mark.asyncio
async def test_send_and_retrieve_message():
    async with httpx.AsyncClient() as client:
        payload = {
            "sender_id": USERS[0]["user_id"],
            "receiver_id": USERS[1]["user_id"],
            "content": "Test deterministic message"
        }
        resp = await client.post(f"{API_BASE}/messages/", json=payload)
        logger.info(f"[test_send_and_retrieve_message] POST response: {resp.json()}")
        assert resp.status_code == 201
        data = resp.json()
        assert data["sender_id"] == USERS[0]["user_id"]
        assert data["receiver_id"] == USERS[1]["user_id"]
        assert data["content"] == "Test deterministic message"
        resp2 = await client.get(f"{API_BASE}/messages/conversation/{CONV_USER1_USER2}")
        logger.info(f"[test_send_and_retrieve_message] GET response: {resp2.json()}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert any(msg["content"] == "Test deterministic message" for msg in data2["data"])