const { spawn } = require('child_process');
const http = require('http');
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
        try { resolve(JSON.parse(data)); } catch (e) { resolve(data); }
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
      await new Promise(r => setTimeout(r, 300));
    }
  }
  throw new Error('Port not reachable');
}

async function run() {
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const profileDir = path.resolve('chrome_profile_err_check');
  const chromeProc = spawn(chromePath, [
    '--remote-debugging-port=9225',
    '--headless=new',
    `--user-data-dir=${profileDir}`,
    '--disable-gpu',
    '--no-first-run',
    'about:blank'
  ]);

  try {
    await waitForPort(9225);
    const newTarget = await httpReq('http://127.0.0.1:9225/json/new?about:blank', 'PUT');
    const ws = new WebSocket(newTarget.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);

    let id = 1;
    const pending = new Map();
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        pending.set(msgId, { resolve, reject });
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    const errors = [];
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id && pending.has(data.id)) {
        const { resolve, reject } = pending.get(data.id);
        pending.delete(data.id);
        if (data.error) reject(data.error);
        else resolve(data.result);
      }
      if (data.method === 'Runtime.exceptionThrown') {
        errors.push({ type: 'exception', details: data.params.exceptionDetails });
      }
      if (data.method === 'Runtime.consoleAPICalled' && data.params.type === 'error') {
        errors.push({ type: 'console.error', args: data.params.args });
      }
    };

    await send('Runtime.enable');
    await send('Page.enable');

    const routes = [
      '/',
      '/login',
      '/authority/dashboard',
      '/authority/incidents',
      '/authority/assignment',
      '/authority/map',
      '/authority/verification',
      '/authority/settings',
      '/admin/dashboard',
      '/admin/incidents',
      '/admin/incidents/CT-1842',
      '/admin/map',
      '/admin/analysis',
      '/admin/sla',
      '/admin/departments',
      '/admin/governance',
      '/admin/settings'
    ];

    for (const r of routes) {
      console.log(`Checking route: ${r}`);
      await send('Page.navigate', { url: `http://localhost:3000${r}` });
      await new Promise(res => setTimeout(res, 500));
    }

    console.log('-----------------------------------------');
    console.log(`TOTAL RUNTIME ERRORS DETECTED: ${errors.length}`);
    if (errors.length > 0) {
      console.log(JSON.stringify(errors, null, 2));
    } else {
      console.log('All 17 routes rendered with 0 exceptions and 0 console errors!');
    }
    console.log('-----------------------------------------');
    ws.close();
  } catch(e) {
    console.error('Check failed:', e);
  } finally {
    try { chromeProc.kill(); } catch(e) {}
  }
}

run();
