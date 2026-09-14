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
  const profileDir = path.resolve('chrome_profile_verify_admin');
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

  console.log('Spawning Chrome for Admin Portal verification...');
  const chromeProc = spawn(chromePath, [
    '--remote-debugging-port=9224',
    '--headless=new',
    `--user-data-dir=${profileDir}`,
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'about:blank'
  ]);

  try {
    await waitForPort(9224);
    console.log('Chrome debugger port 9224 ready.');

    const newTarget = await httpReq('http://127.0.0.1:9224/json/new?about:blank', 'PUT');
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
      if (data.id && pending.has(data.id)) {
        const { resolve, reject } = pending.get(data.id);
        pending.delete(data.id);
        if (data.error) reject(data.error);
        else resolve(data.result);
      }
    };

    await send('Page.enable');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1.5,
      mobile: false
    });

    const routes = [
      { path: '/', out: 'verify_admin_00_landing.png' },
      { path: '/login', out: 'verify_admin_00_login.png' },
      { path: '/admin/dashboard', out: 'verify_admin_01_dashboard.png' },
      { path: '/admin/incidents', out: 'verify_admin_02_incidents.png' },
      { path: '/admin/incidents/CT-1842', out: 'verify_admin_03_incident_detail.png' },
      { path: '/admin/map', out: 'verify_admin_04_map.png' },
      { path: '/admin/analysis', out: 'verify_admin_05_analysis.png' },
      { path: '/admin/sla', out: 'verify_admin_06_sla.png' },
      { path: '/admin/departments', out: 'verify_admin_07_departments.png' },
      { path: '/admin/governance', out: 'verify_admin_08_governance.png' },
      { path: '/admin/settings', out: 'verify_admin_09_settings.png' },
    ];

    for (const r of routes) {
      console.log(`Navigating to http://localhost:3000${r.path}...`);
      await send('Page.navigate', { url: `http://localhost:3000${r.path}` });
      await new Promise(res => setTimeout(res, 1200));

      const screenshot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(r.out, Buffer.from(screenshot.data, 'base64'));
      console.log(`Saved screenshot to ${r.out}`);
    }

    ws.close();
    console.log('All admin screenshots verified and saved!');
  } catch (err) {
    console.error('Verification error:', err);
  } finally {
    try { chromeProc.kill(); } catch (e) {}
  }
}

main();
