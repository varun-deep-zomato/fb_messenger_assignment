# Messenger Application Schema & Design Rationale

## Overview
This document describes the data model, API schema, and design decisions for the FastAPI Messenger application using Cassandra as the backend. It also explains why each table and structure was chosen, and how they support robust, scalable messaging with efficient querying and pagination.

---

## Cassandra Data Model

### Keyspace
- **messenger**: All tables are created under this keyspace for logical grouping.

### Tables

#### 1. `users`
| Column      | Type    | Description         |
|-------------|---------|---------------------|
| user_id     | UUID    | Primary key, unique user identifier |
| username    | text    | Unique username     |

- **Purpose**: Stores all registered users.
- **Reasoning**: Simple lookup for user info; user_id is used as a foreign key in other tables.

#### 2. `conversations_by_user`
| Column         | Type    | Description                       |
|----------------|---------|-----------------------------------|
| user_id        | UUID    | Partition key; user owning the conversation |
| conversation_id| UUID    | Clustering key; unique conversation |
| other_user_id  | UUID    | The other participant in the conversation |
| last_message   | text    | Content of the last message        |
| last_updated   | timestamp | Timestamp of the last message    |

- **Purpose**: Quickly fetch all conversations for a user, sorted by most recent.
- **Reasoning**: Partitioning by user_id enables efficient per-user queries; clustering by conversation_id allows pagination.

#### 3. `messages_by_conversation`
| Column         | Type      | Description                          |
|----------------|-----------|--------------------------------------|
| conversation_id| UUID      | Partition key; the conversation      |
| message_id     | timeuuid  | Clustering key; unique, sortable per message |
| sender_id      | UUID      | Sender of the message                |
| receiver_id    | UUID      | Receiver of the message              |
| content        | text      | Message content                      |
| created_at     | timestamp | When the message was sent            |

- **Purpose**: Fetch all messages for a conversation, support stateless cursor-based pagination.
- **Reasoning**: Partitioning by conversation_id enables efficient conversation queries; clustering by message_id (timeuuid) allows sorting and pagination.

#### 4. `conversation_metadata`
| Column         | Type      | Description                          |
|----------------|-----------|--------------------------------------|
| conversation_id| UUID      | Primary key; unique conversation     |
| created_at     | timestamp | When the conversation was created    |

- **Purpose**: Store metadata for conversations (e.g., creation time).
- **Reasoning**: Needed to support deterministic conversation creation and lookup.

---

## API Endpoints (Summary)
- **/api/conversations/user/{user_id}**: List conversations for a user (paginated)
- **/api/messages/conversation/{conversation_id}**: List messages in a conversation (paginated)
- **/api/messages/send**: Send a message

---

## Pagination Design
- **Cursor-based**: Uses `message_id` (timeuuid) for stateless pagination of messages. The `next_cursor` value is the last message's `id` from the previous page.
- **Reasoning**: Stateless pagination is scalable and works well with Cassandra's clustering keys.

---

## Test Data Generation
- **Script**: `scripts/generate_test_data.py`
- **What it does**: Populates users, conversations, and messages, including edge cases (e.g., empty conversations, single-message conversations, >20 messages for pagination testing).
- **Why**: Ensures robust API and pagination testing, and reproducible results.

---

## Logging
- **All layers**: Logging is implemented in the DB client, models, controllers, and test scripts.
- **Purpose**: Track requests, responses, queries, and errors for easier debugging and monitoring.

---

## Rationale & Best Practices
- **Table design**: Follows Cassandra best practices (wide rows, partition/clustering keys for query patterns).
- **Deterministic conversation IDs**: Ensures idempotent conversation creation between two users.
- **Separation of metadata**: `conversation_metadata` avoids data duplication and supports efficient lookups.
