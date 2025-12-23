from flask import Flask, request, jsonify, send_file
from playwright.async_api import async_playwright
import asyncio
import io
import os
import subprocess
import sys
import requests
import base64

app = Flask(__name__)

# Ensure Playwright browsers are installed
def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to launch chromium to check if it's installed
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            browser.close()
    except Exception as e:
        # If browsers are not installed, install them
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "executable doesn't exist" in error_msg.lower():
            print("Playwright browsers not found. Installing...")
            try:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, timeout=300)
                print("Playwright browsers installed successfully")
            except subprocess.TimeoutExpired:
                print("Warning: Browser installation timed out")
            except Exception as install_error:
                print(f"Warning: Failed to install browsers: {install_error}")

# Install browsers on startup if needed (only runs once)
ensure_playwright_browsers()

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

def upload_to_imgur(image_bytes):
    """Upload image to Imgur and return URL"""
    try:
        # Imgur API endpoint
        url = "https://api.imgur.com/3/image"
        
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Imgur API headers (using anonymous upload - no auth needed)
        headers = {
            'Authorization': 'Client-ID 546c25a59c58ad7'  # Public Imgur client ID
        }
        
        # Upload to Imgur
        response = requests.post(
            url,
            headers=headers,
            data={
                'image': image_b64,
                'type': 'base64'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['link']  # Return the image URL
            else:
                raise Exception(f"Imgur upload failed: {data.get('data', {}).get('error', 'Unknown error')}")
        else:
            raise Exception(f"Imgur API error: {response.status_code}")
            
    except Exception as e:
        raise Exception(f"Failed to upload to Imgur: {str(e)}")

@app.route('/screenshot', methods=['POST'])
def screenshot():
    """Convert HTML to image - returns file or URL based on 'returnUrl' parameter"""
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({"error": "HTML content is required"}), 400
        
        html = data.get('html', '')
        width = int(data.get('width', 1200))
        height = int(data.get('height', 0))
        device_scale_factor = float(data.get('deviceScaleFactor', 2))
        return_url = data.get('returnUrl', False)  # New parameter
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        screenshot_bytes = loop.run_until_complete(
            take_screenshot(html, width, height, device_scale_factor)
        )
        loop.close()
        
        # If returnUrl is True, upload to Imgur and return URL
        if return_url:
            try:
                image_url = upload_to_imgur(screenshot_bytes)
                return jsonify({
                    "success": True,
                    "url": image_url,
                    "message": "Screenshot uploaded successfully"
                })
            except Exception as upload_error:
                # If upload fails, fall back to returning file
                return jsonify({
                    "error": f"Failed to upload image: {str(upload_error)}",
                    "fallback": "Returning file instead"
                }), 500
        
        # Default: Return image file
        return send_file(
            io.BytesIO(screenshot_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name='screenshot.png'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/screenshot-url', methods=['POST'])
def screenshot_url():
    """Convert HTML to image and return URL directly"""
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
        
        # Upload to Imgur and return URL
        image_url = upload_to_imgur(screenshot_bytes)
        
        return jsonify({
            "success": True,
            "url": image_url,
            "message": "Screenshot created and uploaded successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

