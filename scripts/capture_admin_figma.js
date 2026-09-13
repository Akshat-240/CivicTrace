const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

async function httpReq(url, method = 'GET') {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = http.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname + u.search,
      method: method
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

async function waitForPort(port, maxRetries = 25) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await httpReq(`http://127.0.0.1:${port}/json/version`);
      return;
    } catch (e) {
      await new Promise(r => setTimeout(r, 600));
    }
  }
  throw new Error(`Port ${port} not reachable`);
}

async function main() {
  const profileDir = path.resolve('chrome_profile');
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  console.log('Spawning Chrome for Admin Figma...');
  const chromeProc = spawn(chromePath, [
    '--remote-debugging-port=9222',
    '--headless=new',
    `--user-data-dir=${profileDir}`,
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-blink-features=AutomationControlled',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'about:blank'
  ]);

  try {
    await waitForPort(9222);
    const targetUrl = 'https://www.figma.com/design/osJVj6feQxbvVgOqFQo4WS/CivicTrace---Frontend-Design?node-id=0-1&t=BJ3ajXc4blUw7AT6-1';
    console.log('Opening target URL:', targetUrl);
    const newTarget = await httpReq(`http://127.0.0.1:9222/json/new?${encodeURIComponent(targetUrl)}`, 'PUT');

    const ws = new WebSocket(newTarget.webSocketDebuggerUrl);
    let id = 1;
    const pending = new Map();

    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        pending.set(msgId, { resolve, reject });
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id && pending.has(data.id)) {
        const { resolve, reject } = pending.get(data.id);
        pending.delete(data.id);
        if (data.error) reject(data.error);
        else resolve(data);
      }
    };

    await send('Page.enable');
    await send('Page.addScriptToEvaluateOnNewDocument', {
      source: `
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
      `
    });
    await send('Emulation.setDeviceMetricsOverride', {
      width: 2560,
      height: 1440,
      deviceScaleFactor: 1,
      mobile: false
    });

    console.log('Waiting 20s for Figma canvas to load...');
    await new Promise(r => setTimeout(r, 20000));

    // Shift + 1 to zoom to fit all
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await new Promise(r => setTimeout(r, 3000));

    let shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_fit.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_fit.png');

    // Zoom to 100%: Shift + 0
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, windowsVirtualKeyCode: 48, code: 'Digit0', key: ')' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, windowsVirtualKeyCode: 48, code: 'Digit0', key: ')' });
    await new Promise(r => setTimeout(r, 2000));

    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_100.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_100.png');

    // Function to pan
    async function pan(fromX, toX, fromY = 720, toY = 720) {
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: fromX, y: fromY, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: toX, y: toY });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: toX, y: toY, button: 'left' });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await new Promise(r => setTimeout(r, 1000));
    }

    // Pan far left
    for (let i = 0; i < 4; i++) {
      await pan(500, 2200);
    }
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_pan_left.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_pan_left.png');

    // Pan middle
    await pan(2200, 800);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_pan_mid.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_pan_mid.png');

    // Pan right
    await pan(2200, 800);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_pan_right.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_pan_right.png');

    // Pan far right
    await pan(2200, 800);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('admin_figma_pan_far_right.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved admin_figma_pan_far_right.png');

    ws.close();
  } finally {
    chromeProc.kill();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
