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
      await new Promise(r => setTimeout(r, 400));
    }
  }
  throw new Error(`Port ${port} not reachable`);
}

async function main() {
  const profileDir = path.resolve('chrome_profile_verify_fw');
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  console.log('Spawning Chrome for Field Worker Portal verification...');
  const chromeProc = spawn(chromePath, [
    '--remote-debugging-port=9226',
    '--headless=new',
    `--user-data-dir=${profileDir}`,
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank'
  ]);

  const consoleErrors = [];

  try {
    await waitForPort(9226);
    console.log('Chrome debugger port 9226 ready.');

    const newTarget = await httpReq('http://127.0.0.1:9226/json/new?about:blank', 'PUT');
    const ws = new WebSocket(newTarget.webSocketDebuggerUrl);

    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let id = 1;
    const pending = new Map();

    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        pending.set(msgId, { resolve, reject });
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.method === 'Runtime.consoleAPICalled') {
        if (data.params.type === 'error') {
          consoleErrors.push({
            type: 'console.error',
            args: data.params.args.map(a => a.value || a.description)
          });
        }
      }
      if (data.method === 'Runtime.exceptionThrown') {
        consoleErrors.push({
          type: 'exception',
          description: data.params.exceptionDetails?.text || 'Uncaught exception'
        });
      }
      if (data.id && pending.has(data.id)) {
        const { resolve, reject } = pending.get(data.id);
        pending.delete(data.id);
        if (data.error) reject(data.error);
        else resolve(data.result);
      }
    };

    await send('Page.enable');
    await send('Runtime.enable');

    // Desktop viewports
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1.5,
      mobile: false
    });

    // Warm up page
    console.log('Warming up dev server...');
    await send('Page.navigate', { url: 'http://localhost:3000/field-worker/dashboard' });
    await new Promise(res => setTimeout(res, 2000));

    const desktopRoutes = [
      { path: '/field-worker/dashboard', out: 'verify_fw_01_assigned.png' },
      { path: '/field-worker/tasks/CT-INC-024', out: 'verify_fw_02_incident.png' },
      { path: '/field-worker/location', out: 'verify_fw_03_location.png' },
      { path: '/field-worker/evidence', out: 'verify_fw_04_evidence.png' },
      { path: '/field-worker/review', out: 'verify_fw_05_review.png' },
      // Check existing portals
      { path: '/citizen/dashboard', out: 'verify_regression_citizen.png' },
      { path: '/authority/dashboard', out: 'verify_regression_authority.png' },
      { path: '/admin/dashboard', out: 'verify_regression_admin.png' }
    ];

    for (const r of desktopRoutes) {
      console.log(`Navigating to http://localhost:3000${r.path}...`);
      await send('Page.navigate', { url: `http://localhost:3000${r.path}` });
      await new Promise(res => setTimeout(res, 1200));

      const screenshot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(r.out, Buffer.from(screenshot.data, 'base64'));
      console.log(`Saved screenshot to ${r.out}`);
    }

    // Mobile viewport
    await send('Emulation.setDeviceMetricsOverride', {
      width: 390,
      height: 844,
      deviceScaleFactor: 2,
      mobile: true
    });

    const mobileRoutes = [
      { path: '/field-worker/dashboard', out: 'verify_fw_mobile_01_dashboard.png' },
      { path: '/field-worker/tasks/CT-INC-024', out: 'verify_fw_mobile_02_incident.png' },
      { path: '/field-worker/evidence', out: 'verify_fw_mobile_04_evidence.png' }
    ];

    for (const r of mobileRoutes) {
      console.log(`(Mobile) Navigating to http://localhost:3000${r.path}...`);
      await send('Page.navigate', { url: `http://localhost:3000${r.path}` });
      await new Promise(res => setTimeout(res, 1200));

      const screenshot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(r.out, Buffer.from(screenshot.data, 'base64'));
      console.log(`Saved mobile screenshot to ${r.out}`);
    }

    ws.close();
    console.log('--- VERIFICATION RESULT ---');
    if (consoleErrors.length > 0) {
      console.error('Errors encountered during verification:', JSON.stringify(consoleErrors, null, 2));
    } else {
      console.log('SUCCESS: 0 console errors and 0 unhandled exceptions across all tested routes!');
    }
  } catch (err) {
    console.error('Verification script failed:', err);
  } finally {
    try { chromeProc.kill(); } catch (e) {}
  }
}

main();
