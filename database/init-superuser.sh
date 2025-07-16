#!/bin/sh

# Initialize PocketBase superuser from environment variables
# This script creates a superuser before starting the PocketBase server

set -e

echo "Initializing PocketBase superuser..."

# Check if required environment variables are set
if [ -z "$POCKETBASE_ADMIN_EMAIL" ] || [ -z "$POCKETBASE_ADMIN_PASSWORD" ]; then
    echo "Error: POCKETBASE_ADMIN_EMAIL and POCKETBASE_ADMIN_PASSWORD environment variables must be set"
    exit 1
fi

# Create superuser using the upsert command
/pb/pocketbase superuser upsert "$POCKETBASE_ADMIN_EMAIL" "$POCKETBASE_ADMIN_PASSWORD"

echo "Superuser initialized successfully"

# Start PocketBase server
echo "Starting PocketBase server..."
exec /pb/pocketbase serve --http=0.0.0.0:8090