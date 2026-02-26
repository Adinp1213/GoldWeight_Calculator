#!/bin/bash

# Build the project
pip install -r requirements.txt
python manage.py collectstatic --noinput