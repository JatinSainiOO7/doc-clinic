#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies and build CSS
npm install
npm run build

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput