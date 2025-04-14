"""
Sample models for interacting with Cassandra tables.
Students should implement these models based on their database schema design.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from app.db.cassandra_client import cassandra_client

logger = logging.getLogger(__name__)

class MessageModel:
    """
    Message model for interacting with the messages table.
    Students will implement this as part of the assignment.
    
    They should consider:
    - How to efficiently store and retrieve messages
    - How to handle stateless, cursor-based pagination (using message_id as cursor)
    """
    
    # TODO: Implement the following methods
    
    @staticmethod
    async def create_message(conversation_id: str, sender_id: str, receiver_id: str, content: str):
        """
        Create a new message and update conversations_by_user for both participants.
        """
        from datetime import datetime
        import uuid
        from app.db.cassandra_client import cassandra_client

        # Generate message_id as timeuuid
        message_id = uuid.uuid1()
        created_at = datetime.now(datetime.timezone.utc)
        # Insert into messages_by_conversation
        insert_query = (
            "INSERT INTO messages_by_conversation (conversation_id, message_id, sender_id, receiver_id, content, created_at) "
            "VALUES (%(conversation_id)s, %(message_id)s, %(sender_id)s, %(receiver_id)s, %(content)s, %(created_at)s)"
        )
        params = {
            'conversation_id': uuid.UUID(conversation_id),
            'message_id': message_id,
            'sender_id': uuid.UUID(sender_id),
            'receiver_id': uuid.UUID(receiver_id),
            'content': content,
            'created_at': created_at
        }
        cassandra_client.execute(insert_query, params)

        # Update conversations_by_user for both sender and receiver
        update_query = (
            "INSERT INTO conversations_by_user (user_id, conversation_id, last_message, last_updated, other_user_id) "
            "VALUES (%(user_id)s, %(conversation_id)s, %(last_message)s, %(last_updated)s, %(other_user_id)s)"
        )
        for user_id, other_user_id in [
            (sender_id, receiver_id),
            (receiver_id, sender_id)
        ]:
            update_params = {
                'user_id': uuid.UUID(user_id),
                'conversation_id': uuid.UUID(conversation_id),
                'last_message': content,
                'last_updated': created_at,
                'other_user_id': uuid.UUID(other_user_id)
            }
            cassandra_client.execute(update_query, update_params)

        # Optionally, insert into conversation_metadata if not exists
        meta_query = (
            "INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%(conversation_id)s, %(created_at)s) IF NOT EXISTS"
        )
        meta_params = {
            'conversation_id': uuid.UUID(conversation_id),
            'created_at': created_at
        }
        try:
            cassandra_client.execute(meta_query, meta_params)
        except Exception:
            pass  # Ignore if already exists

        return {
            'id': str(message_id),
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'created_at': created_at
        }

    @staticmethod
    async def get_conversation_messages(conversation_id: str, limit: int = 20, last_message_id: str = None):
        """
        Get messages for a conversation with stateless, cursor-based pagination (latest first), using last_message_id for paging.
        """
        from app.db.cassandra_client import cassandra_client
        import uuid
        logger.info(f"[Model] Fetching messages for conversation_id={conversation_id}, limit={limit}, last_message_id={last_message_id}")
        if last_message_id:
            query = (
                "SELECT * FROM messages_by_conversation WHERE conversation_id = %(conversation_id)s AND message_id < %(last_message_id)s ORDER BY message_id DESC LIMIT %(limit)s"
            )
            params = {
                'conversation_id': uuid.UUID(conversation_id),
                'last_message_id': uuid.UUID(last_message_id),
                'limit': limit
            }
        else:
            query = (
                "SELECT * FROM messages_by_conversation WHERE conversation_id = %(conversation_id)s ORDER BY message_id DESC LIMIT %(limit)s"
            )
            params = {
                'conversation_id': uuid.UUID(conversation_id),
                'limit': limit
            }
        logger.info(f"[Model] Query: {query}, Params: {params}")
        rows = cassandra_client.execute(query, params)
        logger.info(f"[Model] Retrieved {len(rows)} rows from Cassandra")
        # Log the first row if available
        if rows:
            logger.info(f"[Model] First row: {rows[0]}")
        else:
            logger.info("[Model] No rows returned")
        return [{'id': str(row['message_id']), 'conversation_id': conversation_id, 'sender_id': str(row['sender_id']), 'receiver_id': str(row['receiver_id']), 'content': row['content'], 'created_at': row['created_at']} for row in rows]

    @staticmethod
    async def get_messages_before_message_id(conversation_id: str, before_message_id: str, page: int = 1, limit: int = 20):
        """
        Get messages before a specific message_id (timeuuid) with pagination.
        """
        from app.db.cassandra_client import cassandra_client
        import uuid
        offset = (page - 1) * limit
        query = (
            "SELECT * FROM messages_by_conversation WHERE conversation_id = %(conversation_id)s AND message_id < %(before_message_id)s ORDER BY message_id DESC LIMIT %(fetch_count)s"
        )
        params = {
            'conversation_id': uuid.UUID(conversation_id),
            'before_message_id': uuid.UUID(before_message_id),
            'fetch_count': offset + limit
        }
        rows = cassandra_client.execute(query, params)
        page_rows = rows[offset:offset+limit]
        return [{'id': str(row['message_id']), 'conversation_id': conversation_id, 'sender_id': str(row['sender_id']), 'receiver_id': str(row['receiver_id']), 'content': row['content'], 'created_at': row['created_at']} for row in page_rows]


class ConversationModel:
    """
    Conversation model for interacting with the conversations-related tables.
    Students will implement this as part of the assignment.
    
    They should consider:
    - How to efficiently store and retrieve conversations for a user
    - How to handle stateless, cursor-based pagination (using conversation_id as cursor)
    - How to optimize for the most recent conversations (using last_updated only for sorting/display, NOT for pagination)
    """
    # TODO: Implement the following methods

    @staticmethod
    async def get_user_conversations(user_id: str, limit: int = 20, before_conversation_id: str = None):
        """
        Get conversations for a user with stateless, cursor-based pagination (using before_conversation_id as cursor).
        """
        from app.db.cassandra_client import cassandra_client
        import uuid
        if before_conversation_id:
            query = (
                "SELECT * FROM conversations_by_user WHERE user_id = %(user_id)s AND conversation_id < %(before_conversation_id)s ORDER BY conversation_id DESC LIMIT %(limit)s"
            )
            params = {
                'user_id': uuid.UUID(user_id),
                'before_conversation_id': uuid.UUID(before_conversation_id),
                'limit': limit
            }
        else:
            query = (
                "SELECT * FROM conversations_by_user WHERE user_id = %(user_id)s ORDER BY conversation_id DESC LIMIT %(limit)s"
            )
            params = {
                'user_id': uuid.UUID(user_id),
                'limit': limit
            }
        rows = cassandra_client.execute(query, params)
        return [{'conversation_id': str(row['conversation_id']), 'user_id': user_id, 'last_message': row['last_message'], 'last_updated': row['last_updated'], 'other_user_id': str(row['other_user_id'])} for row in rows]

    @staticmethod
    async def get_conversation(conversation_id: str):
        """
        Get a conversation by ID from conversation_metadata.
        """
        from app.db.cassandra_client import cassandra_client
        import uuid
        query = "SELECT * FROM conversation_metadata WHERE conversation_id = %(conversation_id)s"
        params = {'conversation_id': uuid.UUID(conversation_id)}
        rows = cassandra_client.execute(query, params)
        if rows:
            return {'conversation_id': conversation_id, 'created_at': rows[0].get('created_at')}
        else:
            return None

    @staticmethod
    async def create_or_get_conversation(user1_id: str, user2_id: str):
        """
        Get an existing conversation between two users or create a new one using a deterministic conversation_id.
        """
        from app.util.util import generate_conversation_id
        from datetime import datetime
        from app.db.cassandra_client import cassandra_client
        import uuid
        conversation_id = generate_conversation_id(user1_id, user2_id)
        # Check if conversation exists
        query = "SELECT * FROM conversation_metadata WHERE conversation_id = %(conversation_id)s"
        params = {'conversation_id': uuid.UUID(conversation_id)}
        rows = cassandra_client.execute(query, params)
        if rows:
            return {'conversation_id': conversation_id, 'created_at': rows[0].get('created_at')}
        # If not exists, create
        created_at = datetime.now(datetime.timezone.utc)
        meta_query = (
            "INSERT INTO conversation_metadata (conversation_id, created_at) VALUES (%(conversation_id)s, %(created_at)s) IF NOT EXISTS"
        )
        meta_params = { 
            'conversation_id': uuid.UUID(conversation_id),
            'created_at': created_at
        }
        cassandra_client.execute(meta_query, meta_params)
        return {'conversation_id': conversation_id, 'created_at': created_at}