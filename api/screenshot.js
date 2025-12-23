const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

let browser = null;

// Configure Chromium for serverless
chromium.setGraphicsMode(false);

async function initBrowser() {
  if (!browser) {
    try {
      const executablePath = await chromium.executablePath();
      
      browser = await puppeteer.launch({
        args: [
          ...chromium.args,
          '--hide-scrollbars',
          '--disable-web-security',
        ],
        defaultViewport: chromium.defaultViewport,
        executablePath,
        headless: chromium.headless,
        ignoreHTTPSErrors: true,
      });
    } catch (error) {
      console.error('Failed to launch browser:', error);
      throw new Error(`Browser initialization failed: ${error.message}`);
    }
  }
  return browser;
}

module.exports = async (req, res) => {
  if (req.method === 'GET') {
    return res.status(200).json({ status: 'ok', message: 'HTML to Image Service is running' });
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const { html, width = 1200, height = 0, deviceScaleFactor = 2 } = req.body || {};

    if (!html) {
      return res.status(400).json({ error: 'HTML content is required' });
    }

    const browserInstance = await initBrowser();
    const page = await browserInstance.newPage();

    try {
      await page.setContent(html, { 
        waitUntil: 'networkidle0',
        timeout: 30000 
      });

      const screenshot = await page.screenshot({
        type: 'png',
        width: parseInt(width),
        height: height ? parseInt(height) : undefined,
        deviceScaleFactor: parseFloat(deviceScaleFactor),
        fullPage: height === 0,
        timeout: 30000
      });

      res.setHeader('Content-Type', 'image/png');
      res.setHeader('Content-Disposition', 'inline; filename=screenshot.png');
      res.setHeader('Cache-Control', 'public, max-age=31536000');
      res.status(200).send(screenshot);
    } finally {
      await page.close();
    }
    
    return;
  } catch (error) {
    console.error('Error in /api/screenshot:', error);
    return res.status(500).json({ 
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
};
