# HTML to Image Service (Python + Playwright)

A simple Python Flask API that converts HTML to PNG images using Playwright.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Run locally:
```bash
python app.py
```

3. Test:
```bash
curl -X POST http://localhost:5000/screenshot \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><body><h1>Test</h1></body></html>","width":1200}'
```

## Deploy to Render.com

See deployment guide below.
