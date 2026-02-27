import os
from pathlib import Path

env_path = Path('.env')
print(f"File exists: {env_path.exists()}")
print(f"File size: {env_path.stat().st_size} bytes")

if env_path.exists():
    print("\n--- First 5 lines ---")
    with open(env_path) as f:
        for i, line in enumerate(f):
            if i < 5:
                # Mask sensitive values
                if '=' in line:
                    key, val = line.strip().split('=', 1)
                    masked = val[:10] + '...' if len(val) > 15 else val
                    print(f"{key}={masked}")
