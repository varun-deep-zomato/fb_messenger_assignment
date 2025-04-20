"""
Script to generate test data for the Messenger application.
This script is a skeleton for students to implement.
"""
import os
import uuid
import logging
import random
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from hashlib import sha256
import uuid

def generate_conversation_id(user1_id: str, user2_id: str) -> str:
    sorted_ids = sorted([user1_id, user2_id])
    hash_input = (sorted_ids[0] + sorted_ids[1]).encode()
    return str(uuid.UUID(sha256(hash_input).hexdigest()[0:32]))

# Cassandra connection settings
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "messenger")

def connect_to_cassandra():
    """Connect to Cassandra cluster."""
    logger.info("Connecting to Cassandra...")
    try:
        cluster = Cluster([CASSANDRA_HOST])
        session = cluster.connect(CASSANDRA_KEYSPACE)
        logger.info("Connected to Cassandra!")
        return cluster, session
    except Exception as e:
        logger.error(f"Failed to connect to Cassandra: {str(e)}")
        raise

def generate_test_data(session):
    """
    Generate robust test data for Messenger with edge cases and pagination scenarios.
    This version is deterministic and uses hardcoded data.
    """
    logger.info("Generating deterministic hardcoded test data...")

    # Hardcoded user UUIDs (as uuid.UUID objects)
    user1_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    user2_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    user3_id = uuid.UUID("33333333-3333-3333-3333-333333333333")

    # Insert users
    session.execute("""
        INSERT INTO users (user_id, username) VALUES (%s, %s)
    """, (user1_id, "alice"))
    session.execute("""
        INSERT INTO users (user_id, username) VALUES (%s, %s)
    """, (user2_id, "bob"))
    session.execute("""
        INSERT INTO users (user_id, username) VALUES (%s, %s)
    """, (user3_id, "carol"))

    # Deterministic conversation between user1 and user2
    conversation_id = uuid.UUID(generate_conversation_id(str(user1_id), str(user2_id)))
    now = datetime(2025, 4, 20, 12, 0, 0)  # Fixed timestamp

    # Insert conversation metadata
    session.execute("""
        INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%s, %s)
    """, (conversation_id, now))

    # Insert conversations_by_user for both users
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user1_id, conversation_id, user2_id, "Hey Bob!", now))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user2_id, conversation_id, user1_id, "Hey Bob!", now))

    # Insert deterministic messages
    from cassandra.util import uuid_from_time
    base_time = datetime(2025, 4, 20, 12, 0, 0)
    messages = [
        {
            "sender_id": user1_id,
            "receiver_id": user2_id,
            "content": "Hey Bob!",
            "created_at": base_time,
        },
        {
            "sender_id": user2_id,
            "receiver_id": user1_id,
            "content": "Hi Alice! How are you?",
            "created_at": base_time + timedelta(minutes=1),
        },
        {
            "sender_id": user1_id,
            "receiver_id": user2_id,
            "content": "I'm good, thanks!",
            "created_at": base_time + timedelta(minutes=2),
        },
    ]
    for i, msg in enumerate(messages):
        msg_id = uuid_from_time(msg["created_at"].timestamp())
        session.execute("""
            INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (conversation_id, msg_id, msg["sender_id"], msg["receiver_id"], msg["content"], msg["created_at"]))

    # --- EDGE CASES ---
    # 1. Empty conversation (no messages)
    empty_convo_id = uuid.UUID(generate_conversation_id(str(user1_id), str(user3_id)))
    empty_convo_time = datetime(2025, 4, 20, 13, 0, 0)
    session.execute("""
        INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%s, %s)
    """, (empty_convo_id, empty_convo_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user1_id, empty_convo_id, user3_id, None, empty_convo_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user3_id, empty_convo_id, user1_id, None, empty_convo_time))

    # 2. Conversation with only one message
    single_msg_convo_id = uuid.UUID(generate_conversation_id(str(user2_id), str(user3_id)))
    single_msg_time = datetime(2025, 4, 20, 14, 0, 0)
    session.execute("""
        INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%s, %s)
    """, (single_msg_convo_id, single_msg_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user2_id, single_msg_convo_id, user3_id, "Yo Carol!", single_msg_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user3_id, single_msg_convo_id, user2_id, "Yo Carol!", single_msg_time))
    msg_id = uuid_from_time(single_msg_time.timestamp())
    session.execute("""
        INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (single_msg_convo_id, msg_id, user2_id, user3_id, "Yo Carol!", single_msg_time))

    # 3. Conversation with many messages (pagination)
    paginated_convo_id = uuid.UUID(generate_conversation_id(str(user1_id), str(user2_id)))
    paginated_base_time = datetime(2025, 4, 20, 15, 0, 0)
    for i in range(25):
        paginated_msg_time = paginated_base_time + timedelta(minutes=i)
        paginated_msg_id = uuid_from_time(paginated_msg_time.timestamp())
        content = f"Paginated message {i+1}"
        session.execute("""
            INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (paginated_convo_id, paginated_msg_id, user1_id if i % 2 == 0 else user2_id,
              user2_id if i % 2 == 0 else user1_id, content, paginated_msg_time))
    # Update last message in conversations_by_user for pagination convo
    session.execute("""
        UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s
    """, ("Paginated message 25", paginated_base_time + timedelta(minutes=24), user1_id, paginated_convo_id))
    session.execute("""
        UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s
    """, ("Paginated message 25", paginated_base_time + timedelta(minutes=24), user2_id, paginated_convo_id))

    # 4. Messages with special/long/empty content in a new convo
    special_convo_id = uuid.UUID(generate_conversation_id(str(user3_id), str(user1_id)))
    special_time = datetime(2025, 4, 20, 16, 0, 0)
    session.execute("""
        INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%s, %s)
    """, (special_convo_id, special_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user3_id, special_convo_id, user1_id, "", special_time))
    session.execute("""
        INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated)
        VALUES (%s, %s, %s, %s, %s)
    """, (user1_id, special_convo_id, user3_id, "", special_time))
    special_msgs = [
        {"content": "", "desc": "empty content"},
        {"content": "!@#$%^&*()_+|~`", "desc": "special characters"},
        {"content": "A"*1000, "desc": "long message"},
        {"content": "Same timestamp", "desc": "same timestamp"},
        {"content": "Same timestamp again", "desc": "same timestamp"},
    ]
    for idx, msg in enumerate(special_msgs):
        t = special_time if "same timestamp" in msg["desc"] else special_time + timedelta(seconds=idx)
        mid = uuid_from_time(t.timestamp())
        session.execute("""
            INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (special_convo_id, mid, user3_id, user1_id, msg["content"], t))

    # 5. User with no conversations (user4)
    user4_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    session.execute("""
        INSERT INTO users (user_id, username) VALUES (%s, %s)
    """, (user4_id, "dave"))

    logger.info("Edge case test data generated.")
    logger.info("Deterministic test data generated.")

def main():
    """Main function to generate test data."""
    cluster = None
    
    try:
        # Connect to Cassandra
        cluster, session = connect_to_cassandra()
        
        # Generate test data
        generate_test_data(session)
        
        logger.info("Test data generation completed successfully!")
    except Exception as e:
        logger.error(f"Error generating test data: {str(e)}")
    finally:
        if cluster:
            cluster.shutdown()
            logger.info("Cassandra connection closed")

if __name__ == "__main__":
    main()