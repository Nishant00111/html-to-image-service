const express = require('express');
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');

const app = express();

app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

let browser = null;

// Initialize browser once
async function initBrowser() {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu'
      ]
    });
  }
  return browser;
}

// Health check endpoint
app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'HTML to Image Service is running' });
});

// Convert HTML to image
app.post('/screenshot', async (req, res) => {
  try {
    const { html, width = 1200, height = 0, deviceScaleFactor = 2 } = req.body;
    
    if (!html) {
      return res.status(400).json({ error: 'HTML content is required' });
    }

    const browserInstance = await initBrowser();
    const page = await browserInstance.newPage();
    
    await page.setContent(html, { waitUntil: 'networkidle0' });
    
    const screenshot = await page.screenshot({
      type: 'png',
      width: width,
      height: height || undefined, // Auto height if 0
      deviceScaleFactor: deviceScaleFactor,
      fullPage: height === 0
    });
    
    await page.close();
    
    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Content-Disposition', 'inline; filename=screenshot.png');
    res.send(screenshot);
    
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  initBrowser(); // Initialize browser on startup
});

