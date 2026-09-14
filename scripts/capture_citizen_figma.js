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

async function waitForPort(port, maxRetries = 20) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await httpReq(`http://127.0.0.1:${port}/json/version`);
      return;
    } catch (e) {
      await new Promise(r => setTimeout(r, 400));
    }
  }
  throw new Error(`Port ${port} not reachable`);
}

async function main() {
  const profileDir = path.resolve('chrome_profile');
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  console.log('Spawning Chrome for Citizen Portal Figma capture...');
  const chromeProc = spawn(chromePath, [
    '--remote-debugging-port=9224',
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
    await waitForPort(9224);
    console.log('Debugger port 9224 ready.');

    const targetUrl = 'https://www.figma.com/design/y3DWe3oMGe1upX9UCc0u91/CivicTrace---Citizen-Portal?node-id=0-1&t=agbpxzzhjIKTtZhQ-1';
    const newTarget = await httpReq(`http://127.0.0.1:9224/json/new?${encodeURIComponent(targetUrl)}`, 'PUT');

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
        else resolve(data.result);
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

    console.log('Waiting 18s for Figma Citizen Portal to load...');
    await new Promise(r => setTimeout(r, 18000));

    // Capture initial overview
    let screenshot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('citizen_figma_overview.png', Buffer.from(screenshot.data, 'base64'));
    console.log('Saved citizen_figma_overview.png');

    // Zoom to fit (Shift + 1)
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 16, key: 'Shift' });
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 49, key: '1' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 49, key: '1' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 16, key: 'Shift' });
    await new Promise(r => setTimeout(r, 2000));

    screenshot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('citizen_figma_fit.png', Buffer.from(screenshot.data, 'base64'));
    console.log('Saved citizen_figma_fit.png');

    // Zoom to 100% (Shift + 0)
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 16, key: 'Shift' });
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 48, key: '0' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 48, key: '0' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 16, key: 'Shift' });
    await new Promise(r => setTimeout(r, 2000));

    screenshot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('citizen_figma_100.png', Buffer.from(screenshot.data, 'base64'));
    console.log('Saved citizen_figma_100.png');

    ws.close();
  } catch (err) {
    console.error('Capture error:', err);
  } finally {
    try { chromeProc.kill(); } catch (e) {}
  }
}

main();
