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

  console.log('Spawning Chrome for Admin targeted captures...');
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

    // Shift + 1 to fit all
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
    await new Promise(r => setTimeout(r, 2000));

    // Let's zoom into specific areas using mouse wheel (Ctrl + wheel or pinch)
    // Or we can click on specific X coordinates at y=750, then press Shift+2 to zoom into that object!
    // In Figma: clicking an object selects it, then Shift+2 zooms to selection!
    // Let's test clicking on each frame!
    // In admin_figma_fit.png (width 2560):
    // Total frames: ~13 frames.
    // Frame positions roughly:
    // Frame 2 (Landing Page): x ≈ 300, y ≈ 750
    // Frame 3 (Login Page): x ≈ 500, y ≈ 750
    // Frame 4 (Admin Command Center): x ≈ 680, y ≈ 750
    // Frame 6 (Admin Incidents List): x ≈ 1080, y ≈ 750
    // Frame 7 (Admin Incident Detail): x ≈ 1280, y ≈ 750
    // Frame 8 (Admin Map Page): x ≈ 1470, y ≈ 750
    // Frame 9 (Admin Analytics Page): x ≈ 1660, y ≈ 750
    // Frame 10 (Admin SLA Monitoring): x ≈ 1850, y ≈ 750
    // Frame 11 (Admin Department Page): x ≈ 2040, y ≈ 750
    // Frame 12 (Admin Review and Governance): x ≈ 2230, y ≈ 750
    // Frame 13 (Admin Settings): x ≈ 2420, y ≈ 750

    const targets = [
      { name: 'landing_page', x: 300, y: 750 },
      { name: 'login_page', x: 480, y: 750 },
      { name: 'admin_command_center', x: 680, y: 750 },
      { name: 'admin_incidents_list', x: 1080, y: 750 },
      { name: 'admin_incident_detail', x: 1280, y: 750 },
      { name: 'admin_map_page', x: 1470, y: 750 },
      { name: 'admin_analytics_page', x: 1660, y: 750 },
      { name: 'admin_sla_monitoring', x: 1850, y: 750 },
      { name: 'admin_department_page', x: 2040, y: 750 },
      { name: 'admin_review_governance', x: 2230, y: 750 },
      { name: 'admin_settings', x: 2420, y: 750 }
    ];

    for (const tgt of targets) {
      console.log(`Focusing on ${tgt.name}...`);
      // First Shift+1 to ensure baseline
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, windowsVirtualKeyCode: 49, code: 'Digit1', key: '!' });
      await new Promise(r => setTimeout(r, 1000));

      // Click on target
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: tgt.x, y: tgt.y, button: 'left', clickCount: 1 });
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: tgt.x, y: tgt.y, button: 'left' });
      await new Promise(r => setTimeout(r, 500));

      // Shift + 2: Zoom to selection
      await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, windowsVirtualKeyCode: 50, code: 'Digit2', key: '@' });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, windowsVirtualKeyCode: 50, code: 'Digit2', key: '@' });
      await new Promise(r => setTimeout(r, 2000));

      const shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`admin_${tgt.name}.png`, Buffer.from(shot.result.data, 'base64'));
      console.log(`Saved admin_${tgt.name}.png`);
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
