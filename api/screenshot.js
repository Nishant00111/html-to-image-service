const puppeteer = require('puppeteer-core');
const chromium = require('@sparticuz/chromium');

let browser = null;

// Configure Chromium for serverless
chromium.setGraphicsMode(false);
chromium.setHeadlessMode(true);

async function initBrowser() {
  if (!browser) {
    try {
      console.log('Starting Chromium initialization...');
      
      // Get executable path with error handling
      let executablePath;
      try {
        executablePath = await chromium.executablePath();
        console.log('Chromium executable path obtained');
      } catch (pathError) {
        console.error('Failed to get executable path:', pathError);
        throw new Error(`Chromium executable path error: ${pathError.message}`);
      }
      
      if (!executablePath) {
        throw new Error('Chromium executable path is null or undefined');
      }
      
      console.log('Launching Puppeteer...');
      
      // Launch browser with timeout
      browser = await Promise.race([
        puppeteer.launch({
          args: chromium.args,
          defaultViewport: chromium.defaultViewport,
          executablePath,
          headless: chromium.headless,
          ignoreHTTPSErrors: true,
        }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Browser launch timeout after 25 seconds')), 25000)
        )
      ]);
      
      console.log('Browser launched successfully');
      
      // Test browser is working
      const testPage = await browser.newPage();
      await testPage.close();
      console.log('Browser test successful');
      
    } catch (error) {
      console.error('Browser initialization error:', error);
      console.error('Error stack:', error.stack);
      browser = null; // Reset so we can retry
      throw error;
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
