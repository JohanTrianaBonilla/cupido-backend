#!/bin/bash
echo "🔄 Running migrations..."
python manage.py makemigrations notificacion_app
python manage.py migrate
echo "🚀 Starting Daphne server..."
exec daphne \
    -b 0.0.0.0 \
    -p 8000 \
    --proxy-headers \
    --websocket_timeout 3600 \
    --ping-interval 20 \
    --ping-timeout 10 \
    --access-log - \
    --verbosity 1 \
    config.asgi:application
