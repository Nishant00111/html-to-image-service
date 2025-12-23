from flask import Flask, request, jsonify, send_file
from playwright.async_api import async_playwright
import asyncio
import io
import os
import subprocess
import sys
import base64
import uuid
from datetime import datetime, timedelta
from threading import Lock

app = Flask(__name__)

# In-memory storage for temporary images (for serving via URL)
# In production, consider using Redis or a file system with cleanup
image_storage = {}
image_storage_lock = Lock()
IMAGE_EXPIRY_HOURS = 24  # Images expire after 24 hours

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
    # Clean up expired images on health check
    expired_count = cleanup_expired_images()
    return jsonify({
        "status": "ok",
        "message": "HTML to Image Service is running",
        "routes": ["/screenshot", "/screenshot-url"],
        "images_stored": len(image_storage),
        "expired_cleaned": expired_count
    })

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
        
        # If returnUrl is True, return base64 data URL (no external service needed)
        if return_url:
            # Convert to base64 data URL
            image_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            data_url = f"data:image/png;base64,{image_b64}"
            
            return jsonify({
                "success": True,
                "url": data_url,
                "format": "data_url",
                "message": "Screenshot created successfully (base64 data URL)"
            })
        
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
    """Convert HTML to image and return HTTP URL (stored temporarily on server)"""
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
        
        # Generate unique ID for this image
        image_id = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=IMAGE_EXPIRY_HOURS)
        
        # Store image in memory
        with image_storage_lock:
            image_storage[image_id] = {
                'data': screenshot_bytes,
                'expiry': expiry_time,
                'created': datetime.now()
            }
        
        # Get base URL from request
        base_url = request.url_root.rstrip('/')
        image_url = f"{base_url}/image/{image_id}"
        
        return jsonify({
            "success": True,
            "url": image_url,
            "format": "http_url",
            "message": "Screenshot created successfully",
            "expires_in_hours": IMAGE_EXPIRY_HOURS
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/image/<image_id>', methods=['GET'])
def serve_image(image_id):
    """Serve a temporarily stored image by ID"""
    try:
        with image_storage_lock:
            if image_id not in image_storage:
                return jsonify({"error": "Image not found"}), 404
            
            image_data = image_storage[image_id]
            
            # Check if expired
            if datetime.now() > image_data['expiry']:
                # Clean up expired image
                del image_storage[image_id]
                return jsonify({"error": "Image has expired"}), 410
            
            # Return the image
            return send_file(
                io.BytesIO(image_data['data']),
                mimetype='image/png',
                as_attachment=False,
                download_name='screenshot.png'
            )
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cleanup_expired_images():
    """Clean up expired images (call this periodically)"""
    with image_storage_lock:
        now = datetime.now()
        expired_ids = [
            img_id for img_id, img_data in image_storage.items()
            if now > img_data['expiry']
        ]
        for img_id in expired_ids:
            del image_storage[img_id]
        return len(expired_ids)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

