#!/bin/bash
pip install -r requirements.txt -q
python -m playwright install chromium
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
