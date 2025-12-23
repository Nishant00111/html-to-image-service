from playwright.async_api import async_playwright
import json
import base64
from http.server import BaseHTTPRequestHandler

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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            "status": "ok",
            "message": "HTML to Image Service is running",
            "routes": ["/api/screenshot"]
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        import asyncio
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract parameters
            html = data.get('html', '')
            width = int(data.get('width', 1200))
            height = int(data.get('height', 0))
            device_scale_factor = float(data.get('deviceScaleFactor', 2))
            
            if not html:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "HTML content is required"}).encode())
                return
            
            # Take screenshot
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            screenshot = loop.run_until_complete(
                take_screenshot(html, width, height, device_scale_factor)
            )
            loop.close()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Disposition', 'inline; filename=screenshot.png')
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            self.wfile.write(screenshot)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())

