#!/bin/bash

echo "======================================"
echo "    ERP-EDUCATIVA SYSTEM DIAGNOSTIC    "
echo "======================================"
echo ""

echo "1. Checking System Resources..."
echo "-------------------------------"
df -h | grep -E '^Filesystem|/dev/'
echo ""
free -m
echo ""

echo "2. Checking PostgreSQL Database..."
echo "----------------------------------"
# Using a common postgres ping method if psql isn't directly available or auth is tricky
# We'll check if the port 5432 is listening
if ss -tuln | grep -q ":5432 "; then
    echo "✅ PostgreSQL port (5432) is listening."
else
    echo "❌ PostgreSQL port (5432) is NOT listening!"
fi
echo ""

echo "3. Checking Redis (Celery/Cache)..."
echo "-----------------------------------"
if ss -tuln | grep -q ":6379 "; then
    echo "✅ Redis port (6379) is listening."
else
    echo "❌ Redis port (6379) is NOT listening (Might be normal if not used locally)."
fi
echo ""

echo "4. Checking Application Processes..."
echo "------------------------------------"
python_procs=$(pgrep -f "python.*manage.py runserver" | wc -l)
if [ "$python_procs" -gt 0 ]; then
    echo "✅ Django development server is running."
else
    echo "⚠️ Django development server does not appear to be running."
fi

node_procs=$(pgrep -f "node.*vite" | wc -l)
if [ "$node_procs" -gt 0 ]; then
    echo "✅ Vite frontend server is running."
else
    echo "⚠️ Vite frontend server does not appear to be running."
fi
echo ""

echo "5. Checking Backend Logs (last 10 lines)..."
echo "-------------------------------------------"
if [ -f "/tmp/django_debug.log" ]; then
    tail -n 10 /tmp/django_debug.log
else
    echo "No debug log found at /tmp/django_debug.log (This might be normal)."
fi
echo ""

echo "Diagnostic Complete."
echo "======================================"
