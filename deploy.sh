#!/bin/bash

echo "Building CSS..."
npm run build

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Running migrations..."
python manage.py migrate --noinput

echo "Deployment preparation complete!"