from hashlib import sha256
import uuid

def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    sorted_ids = sorted([user1_id, user2_id])
    hash_input = (sorted_ids[0] + sorted_ids[1]).encode()
    return str(uuid.UUID(sha256(hash_input).hexdigest()[0:32]))
