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

  console.log('Spawning Chrome for Admin far right capture...');
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
    await send('Emulation.setDeviceMetricsOverride', {
      width: 2560,
      height: 1440,
      deviceScaleFactor: 1,
      mobile: false
    });

    console.log('Waiting 18s for Figma to load...');
    await new Promise(r => setTimeout(r, 18000));

    // Zoom to 100%: Ctrl + 0
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 2, windowsVirtualKeyCode: 48, code: 'Digit0', key: '0' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 2, windowsVirtualKeyCode: 48, code: 'Digit0', key: '0' });
    await new Promise(r => setTimeout(r, 2000));

    async function pan(fromX, toX, fromY = 720, toY = 720) {
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: fromX, y: fromY, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: toX, y: toY });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: toX, y: toY, button: 'left' });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await new Promise(r => setTimeout(r, 800));
    }

    // Pan to seg 8 baseline
    for (let s = 1; s <= 8; s++) {
      await pan(2200, 600);
    }

    // Now pan right further to capture Department Page, Review & Governance, Settings
    for (let s = 9; s <= 13; s++) {
      await pan(2200, 600);
      let shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`admin_seg_${s}.png`, Buffer.from(shot.result.data, 'base64'));
      console.log(`Saved admin_seg_${s}.png`);
    }

    ws.close();
  } finally {
    chromeProc.kill();
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
