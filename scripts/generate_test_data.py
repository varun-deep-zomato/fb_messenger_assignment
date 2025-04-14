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
    """
    logger.info("Generating comprehensive test data...")
    import uuid
    from datetime import datetime, timedelta

    # --- USERS ---
    users = [
        {"user_id": uuid.UUID("11111111-1111-1111-1111-111111111111"), "username": "alice"},
        {"user_id": uuid.UUID("22222222-2222-2222-2222-222222222222"), "username": "bob"},
        {"user_id": uuid.UUID("33333333-3333-3333-3333-333333333333"), "username": "carol"},
        {"user_id": uuid.UUID("44444444-4444-4444-4444-444444444444"), "username": "dave"},
        {"user_id": uuid.UUID("55555555-5555-5555-5555-555555555555"), "username": "eve"},
    ]
    for user in users:
        session.execute(
            "INSERT INTO users (user_id, username) VALUES (%s, %s)",
            (user["user_id"], user["username"])
        )
    logger.info("Inserted users: alice, bob, carol, dave, eve")

    # --- CONVERSATIONS ---
    conversations = [
        # Alice & Bob
        {"id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), "user1_id": users[0]["user_id"], "user2_id": users[1]["user_id"]},
        # Alice & Carol
        {"id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), "user1_id": users[0]["user_id"], "user2_id": users[2]["user_id"]},
        # Bob & Dave
        {"id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"), "user1_id": users[1]["user_id"], "user2_id": users[3]["user_id"]},
        # Carol & Eve
        {"id": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"), "user1_id": users[2]["user_id"], "user2_id": users[4]["user_id"]},
        # Alice & Eve (empty conversation, edge case)
        {"id": uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"), "user1_id": users[0]["user_id"], "user2_id": users[4]["user_id"]},
    ]
    now = datetime.utcnow()
    for convo in conversations:
        # Insert into conversation_metadata
        session.execute(
            "INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%s, %s)",
            (convo["id"], now)
        )
        # Insert into conversations_by_user for both users
        for user, other in [(convo["user1_id"], convo["user2_id"]), (convo["user2_id"], convo["user1_id"])]:
            session.execute(
                "INSERT INTO conversations_by_user (user_id, conversation_id, other_user_id, last_message, last_updated) VALUES (%s, %s, %s, %s, %s)",
                (user, convo["id"], other, None, now)
            )
    logger.info("Inserted conversations and metadata for all users")

    # --- MESSAGES (with pagination edge cases) ---
    # Alice & Bob: 25 messages (tests pagination > 20)
    for i in range(25):
        sender = users[0]["user_id"] if i % 2 == 0 else users[1]["user_id"]
        receiver = users[1]["user_id"] if i % 2 == 0 else users[0]["user_id"]
        content = f"Message {i+1} between alice and bob"
        created_at = now - timedelta(minutes=25-i)
        message_id = uuid.uuid1()
        session.execute(
            "INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (conversations[0]["id"], message_id, sender, receiver, content, created_at)
        )
        # Update last_message and last_updated in conversations_by_user for both users
        for user, other in [(sender, receiver), (receiver, sender)]:
            session.execute(
                "UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s",
                (content, created_at, user, conversations[0]["id"])
            )
    # Alice & Carol: 1 message (edge: single message)
    sender = users[0]["user_id"]
    receiver = users[2]["user_id"]
    content = "Hello Carol!"
    created_at = now
    message_id = uuid.uuid1()
    session.execute(
        "INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (conversations[1]["id"], message_id, sender, receiver, content, created_at)
    )
    for user, other in [(sender, receiver), (receiver, sender)]:
        session.execute(
            "UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s",
            (content, created_at, user, conversations[1]["id"])
        )
    # Bob & Dave: 10 messages
    for i in range(10):
        sender = users[1]["user_id"] if i % 2 == 0 else users[3]["user_id"]
        receiver = users[3]["user_id"] if i % 2 == 0 else users[1]["user_id"]
        content = f"Message {i+1} between bob and dave"
        created_at = now - timedelta(minutes=10-i)
        message_id = uuid.uuid1()
        session.execute(
            "INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (conversations[2]["id"], message_id, sender, receiver, content, created_at)
        )
        for user, other in [(sender, receiver), (receiver, sender)]:
            session.execute(
                "UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s",
                (content, created_at, user, conversations[2]["id"])
            )
    # Carol & Eve: 2 messages
    for i in range(2):
        sender = users[2]["user_id"] if i % 2 == 0 else users[4]["user_id"]
        receiver = users[4]["user_id"] if i % 2 == 0 else users[2]["user_id"]
        content = f"Message {i+1} between carol and eve"
        created_at = now - timedelta(minutes=2-i)
        message_id = uuid.uuid1()
        session.execute(
            "INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (conversations[3]["id"], message_id, sender, receiver, content, created_at)
        )
        for user, other in [(sender, receiver), (receiver, sender)]:
            session.execute(
                "UPDATE conversations_by_user SET last_message=%s, last_updated=%s WHERE user_id=%s AND conversation_id=%s",
                (content, created_at, user, conversations[3]["id"])
            )
    # No messages for Alice & Eve (edge: empty conversation)
    logger.info("Test data generation completed.")

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