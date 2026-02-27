#!/bin/bash
# MEX BALANCER PRO - Verification & Push Script

echo "🔍 VERIFYING SYSTEM..."

# Check files exist
files=("main.py" "requirements.txt" "Procfile" "runtime.txt" "health_server.py" ".env")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
        exit 1
    fi
done

# Check .env has variables
echo ""
echo "🔐 CHECKING ENV VARIABLES..."
if grep -q "BOT_TOKEN" .env && grep -q "SOL_MAIN" .env; then
    echo "✅ Environment variables present"
else
    echo "❌ .env is empty or missing variables!"
    exit 1
fi

# Check .env is in .gitignore
if grep -q ".env" .gitignore; then
    echo "✅ .env protected by .gitignore"
else
    echo "⚠️  WARNING: .env not in .gitignore"
fi

# Git status
echo ""
echo "📤 GIT STATUS..."
git status --short

# Commit and push
echo ""
echo "🚀 PUSHING TO GITHUB..."
git add -A
git commit -m "MEX BALANCER PRO v1.0 - Production Ready MEV Bot
- Pure Python, no dependency conflicts
- Jupiter API integration for swaps
- Jito MEV protection
- Auto TP/SL logic
- Revenue tracking
- Channel notifications"

git push origin main

echo ""
echo "✅ PUSHED SUCCESSFULLY!"
echo ""
echo "📋 RENDER DEPLOYMENT SETTINGS:"
echo "Build Command: pip install -r requirements.txt"
echo "Start Command: python main.py"
echo ""
echo "🔐 ENVIRONMENT VARIABLES TO PASTE:"
cat .env
