# HTML to Image Service

A free, self-hosted HTML to Image converter using Puppeteer.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run locally:
```bash
npm start
```

3. Test the service:
```bash
curl -X POST http://localhost:3000/screenshot \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><body><h1>Test</h1></body></html>","width":1200,"deviceScaleFactor":2}'
```

## Deploy to Render.com

1. Push this code to a GitHub repository
2. Go to https://render.com
3. Sign up/login
4. Click "New" → "Web Service"
5. Connect your GitHub repo
6. Settings:
   - **Build Command**: `npm install`
   - **Start Command**: `node server.js`
   - **Environment**: Node
7. Click "Create Web Service"
8. Copy the URL (e.g., your-service.onrender.com)

## API Usage

**Endpoint**: `POST /screenshot`

**Request Body**:
```json
{
  "html": "<html><body><h1>Hello World</h1></body></html>",
  "width": 1200,
  "height": 0,
  "deviceScaleFactor": 2
}
```

**Response**: PNG image

**Parameters**:
- `html` (required): HTML content to convert
- `width` (optional): Image width in pixels (default: 1200)
- `height` (optional): Image height in pixels (0 = auto height, default: 0)
- `deviceScaleFactor` (optional): Image scale factor (default: 2)

## Notes

- Render.com free tier includes 750 hours/month
- Service may spin down after inactivity (takes ~30 seconds to wake up)
- For production, consider upgrading to a paid plan for always-on service

