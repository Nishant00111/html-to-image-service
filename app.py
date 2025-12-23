from flask import Flask, request, jsonify, send_file
from playwright.async_api import async_playwright
import asyncio
import io
import os

app = Flask(__name__)

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

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "HTML to Image Service is running",
        "routes": ["/screenshot"]
    })

@app.route('/screenshot', methods=['POST'])
def screenshot():
    """Convert HTML to image"""
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({"error": "HTML content is required"}), 400
        
        html = data.get('html', '')
        width = int(data.get('width', 1200))
        height = int(data.get('height', 0))
        device_scale_factor = float(data.get('deviceScaleFactor', 2))
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot_bytes = loop.run_until_complete(
            take_screenshot(html, width, height, device_scale_factor)
        )
        loop.close()
        
        # Return image
        return send_file(
            io.BytesIO(screenshot_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name='screenshot.png'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

