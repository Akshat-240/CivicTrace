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
      await new Promise(r => setTimeout(r, 500));
    }
  }
  throw new Error(`Port ${port} not reachable`);
}

async function main() {
  const profileDir = path.resolve('chrome_profile');
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  console.log('Spawning Chrome for Field Worker Precise Capture...');
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
    const targetUrl = 'https://www.figma.com/design/Dj6Yr0kt8SYQX1dIHJKkJK/CivicTrace-%E2%80%94-Field-Worker-Portal-%E2%80%94-New?node-id=0-1&p=f&t=HLc9qH02XFDdm8A5-0';
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

    // Zoom to fit (Shift + 1)
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 2, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 2, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await new Promise(r => setTimeout(r, 2000));

    // Zoom in once to make text very readable
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 2, windowsVirtualKeyCode: 187, code: 'Equal', key: '+' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 2, windowsVirtualKeyCode: 187, code: 'Equal', key: '+' });
    await new Promise(r => setTimeout(r, 1000));

    async function dragCanvas(dx) {
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 1280, y: 720, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 1280 + dx, y: 720 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 1280 + dx, y: 720, button: 'left' });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', code: 'Space', key: ' ', windowsVirtualKeyCode: 32 });
      await new Promise(r => setTimeout(r, 800));
    }

    // First pan far left
    for (let i = 0; i < 4; i++) {
      await dragCanvas(1000);
    }
    let shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('fw_screen_1_assigned.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved fw_screen_1_assigned.png');

    // Pan to screen 2
    await dragCanvas(-650);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('fw_screen_2_incident.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved fw_screen_2_incident.png');

    // Pan to screen 3
    await dragCanvas(-650);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('fw_screen_3_location.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved fw_screen_3_location.png');

    // Pan to screen 4
    await dragCanvas(-650);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('fw_screen_4_evidence.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved fw_screen_4_evidence.png');

    // Pan to screen 5
    await dragCanvas(-650);
    shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('fw_screen_5_review.png', Buffer.from(shot.result.data, 'base64'));
    console.log('Saved fw_screen_5_review.png');

    ws.close();
  } finally {
    try { chromeProc.kill(); } catch (e) {}
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
