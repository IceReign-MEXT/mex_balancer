#!/bin/bash
# Deployment script for Render

echo "🚀 Setting up MEX BALANCER..."

# Create directories
mkdir -p logs

# Install dependencies
pip install -r requirements.txt

# Initialize database (run once)
python -c "
import asyncio
from core.database import DatabaseManager
from core.config import Config

async def init():
    config = Config()
    db = DatabaseManager(config.database_url)
    await db.connect()
    print('✅ Database initialized')

asyncio.run(init())
"

echo "✅ Setup complete. Starting bot..."
python main.py
