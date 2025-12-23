from playwright.async_api import async_playwright
import json
import asyncio

async def take_screenshot(html_content, width=1200, height=0, device_scale_factor=2):
    """Take a screenshot of HTML content using Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        page = await browser.new_page()
        
        # Set viewport
        if height == 0:
            await page.set_viewport_size({"width": width, "height": 800})
        else:
            await page.set_viewport_size({"width": width, "height": height})
        
        # Set content
        await page.set_content(html_content, wait_until="networkidle")
        
        # Take screenshot
        screenshot = await page.screenshot(
            type="png",
            full_page=(height == 0)
        )
        
        await browser.close()
        return screenshot

def handler(req):
    """Vercel serverless function handler"""
    import base64
    
    # Handle GET requests
    if req.method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "status": "ok",
                "message": "HTML to Image Service is running",
                "routes": ["/api/screenshot"]
            })
        }
    
    # Handle POST requests
    if req.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Method Not Allowed"})
        }
    
    try:
        # Parse request body
        data = json.loads(req.body) if isinstance(req.body, str) else req.body
        
        # Extract parameters
        html = data.get('html', '')
        width = int(data.get('width', 1200))
        height = int(data.get('height', 0))
        device_scale_factor = float(data.get('deviceScaleFactor', 2))
        
        if not html:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "HTML content is required"})
            }
        
        # Take screenshot (run async function)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot = loop.run_until_complete(
            take_screenshot(html, width, height, device_scale_factor)
        )
        loop.close()
        
        # Convert to base64 for response
        screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/png',
                'Content-Disposition': 'inline; filename=screenshot.png',
                'Cache-Control': 'public, max-age=31536000'
            },
            'body': screenshot_b64,
            'isBase64Encoded': True
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": str(e)})
        }

