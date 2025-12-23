const puppeteer = require('puppeteer');

let browser = null;

async function initBrowser() {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--single-process',
        '--no-zygote'
      ],
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
    });
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

    await page.setContent(html, { waitUntil: 'networkidle0' });

    const screenshot = await page.screenshot({
      type: 'png',
      width,
      height: height || undefined,
      deviceScaleFactor,
      fullPage: height === 0,
    });

    await page.close();

    res.setHeader('Content-Type', 'image/png');
    res.setHeader('Content-Disposition', 'inline; filename=screenshot.png');
    res.status(200).send(screenshot);
    return;
  } catch (error) {
    console.error('Error in /api/screenshot:', error);
    return res.status(500).json({ error: error.message });
  }
};
