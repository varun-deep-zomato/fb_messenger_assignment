#!/bin/bash
# Cleanup script to drop the 'messenger' keyspace from Cassandra (Docker)

set -e

CONTAINER_NAME=${1:-cassandra}
KEYSPACE=${2:-messenger}

# Drop the keyspace using cqlsh inside the container
echo "Dropping keyspace '$KEYSPACE' in container '$CONTAINER_NAME'..."
docker exec -i "$CONTAINER_NAME" cqlsh -e "DROP KEYSPACE IF EXISTS $KEYSPACE;"
echo "Keyspace '$KEYSPACE' dropped successfully."