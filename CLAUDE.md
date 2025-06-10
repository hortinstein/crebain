# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ungoliant is a multi-service command & control (C2) platform for agent management with encrypted communications, AI-assisted operations, and real-time monitoring. Named after Tolkien's dark primordial creature, it consists of five main layers working together to provide a complete agent orchestration system.

## Architecture

### Core Components
- **Database Layer** (`/database/`) - Central data management, API endpoints, task dispatching
- **Endpoint Layer** (`/endpoint/nim/`) - Compiled agent binaries written in Nim, C, Zig, rust, go
- **Interface Layer** (`/interface/`) - Streamlit-based web dashboard
- **Middleware Layer** (`/middleware/`) - S3 storage and supporting services  
- **Simulation Layer** (`/simulation/`) - Dockerized development environment

### Technology Stack
- **Database**: PocketBase database
- **Agents**: Targeting small, fast and cross platform compiled binaries like the Nim, C, Zig, rust, go
- **Frontend**: NiceUI python
- **Storage**: S3-compatible (LocalStack for development)
- **AI**: claude
- **Infrastructure**: Docker Compose orchestration

## Development Commands

### Initial Environment Setup
```bash
# Build core services
cd database 
docker build -t dispatcher -f Dockerfile.dispatcher .
docker build -t staging -f Dockerfile.staging .

# Start simulation environment
cd simulation           
docker-compose up -d    # starts simulated docker network
python generate_ips.py  # randomizes IPs for realistic testing
```

### Agent Development (Nim)
```bash
cd endpoint/nim
nimble buildall    # Build all components including Python interop
nimble testall     # Run comprehensive tests
nimble buildwin    # Cross-compile for Windows
nimble buildmobile # Cross-compile for ARM64
```

### Development Reset
```bash
cd simulation
./bootstrap_debug.sh  # WARNING: Destroys pb_data/ and restarts services
```

## Required Environment Files

### `database/.env`
```
POCKETBASE_URL="http://localhost:8090/"
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
IPINFO_TOKEN=""  # Get from https://ipinfo.io/account/token
```

### `interface/.env`
```
POCKETBASE_URL="http://localhost:8090/"
STREAMLIT_ENV="dev"
DEV_USER="user_test"
DEV_PASSWORD="testtest"
```

### `ai/.env`
```
GROQ_API_KEY=""  # Get from https://console.groq.com/keys
```

### `middleware/s3/.env`
```
AWS_ENDPOINT_URL="http://localhost:4566"
AWS_ACCESS_KEY_ID="test"
AWS_SECRET_ACCESS_KEY="tester"
AWS_REGION="us-east-1"
DATA_BUCKET="your-data-bucket-name"
CONTROL_BUCKET="your-control-bucket-name"
```

## Key Architecture Patterns

### Agent Communication
- End-to-end encryption using Monocypher
- Binary configuration with public/private keys
- S3-based command and control channels
- Real-time callback processing and storage

### Database Schema
Core entities: Users, Agent Groups, Configured Agents, Reference Agents, Callbacks, Tasks with bidirectional relationships managed through PocketBase.

### Service Integration
- Nim agents compile to small binaries with Python interop via `common_lib`
- Streamlit interface connects to PocketBase for data and authentication
- Docker services communicate through shared networks and volumes
- AI integration uses structured prompts for operational assistance

### Development Considerations
- PocketBase v0.28.3 is the current version (uses `_superusers` collection instead of deprecated `/api/admins`)
- Cross-compilation requires proper Nim toolchain setup
- The `common_lib` component bridges Nim and Python ecosystems
- All services expect local development with LocalStack S3 simulation

## Recent Development Focus
The project has been actively developed with recent emphasis on S3 integration, AI-assisted tasking, real-time notifications, and containerization of core services.