'use strict';
/*
 * brewdesk server — LBW 破甲工作台 · 本地复刻版
 *
 * 反向说明：
 *   原版是 Electron 应用，src/main.js 只做三件事：创建窗口、注册 IPC handler、
 *   把 Electron 的 dialog/shell 结果转交给 src/lib/* 里的纯 Node 引擎。
 *   所有业务逻辑（席位包渲染、部署事务、备份恢复、激活门、任务契约、中转、
 *   工作流、IDA 工具箱、完整技能包）都在 src/lib 与 src/shared 中，且不依赖
 *   Electron（只有 main.js / preload.js 引用了 electron）。
 *
 *   本文件用零依赖的 node:http 复刻 main.js 的 IPC 表：同一批 handler、同样的
 *   参数形状、同样的返回结构，把 dialog/shell 换成服务端原生对话框与系统打开。
 *   页面侧由 src/bridge.js 把 window.coldbrew 映射到 POST /api/invoke。
 */

const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');

const ROOT = __dirname;
const PORT = Number(process.env.BREWDESK_PORT || 8788);
const DATA_DIR = process.env.BREWDESK_HOME || path.join(os.homedir(), '.brewdesk');
let activePort = PORT;
const PERSIST_KEY = process.env.BREWDESK_PERSIST_KEY === '1' || process.argv.includes('--persist');
const TOOLBOX_ROOT = path.join(ROOT, 'resources', 'toolbox');

/* ---------------------------------------------------------------- 引擎加载 */
const { ACTIVATION_WORD, CONTROL_WORD, APP_TITLE, PROFILES, SEATS, CHANNELS, activate } = require('./src/lib/prompt-engine');
const workbenchCore = require('./src/shared/workbench-core');
const geminiSeat = require('./src/lib/gemini-seat');
const seatRuntime = require('./src/lib/seat-runtime');
const { SeatTransactions } = require('./src/lib/seat-transactions');
const { ActivationGate } = require('./src/lib/activation-gate');
const { detectDirectory } = require('./src/lib/detect-directory');
const beginner = require('./src/lib/beginner-install');
const idaToolbox = require('./src/lib/ida-toolbox');
const idaMcp = require('./src/lib/ida-mcp');
const upstreamSkills = require('./src/lib/upstream-skills');
const { WorkflowEngine, planWorkflow, healthCheckTools } = require('./src/lib/workflow');
const { RelayAdapter } = require('./src/lib/relay-adapter');
const { ToolboxEngine } = require(TOOLBOX_ROOT + '/engine.js');
const { runAgent } = require(TOOLBOX_ROOT + '/agent.js');

const seatTransactions = new SeatTransactions();
const activationGate = new ActivationGate();
const relayAdapter = new RelayAdapter();

const COMMUNITY = {
  tg: [
    { name: 'TG 频道', value: 'https://t.me/lbwapi', href: 'https://t.me/lbwapi' },
    { name: 'TG 私聊', value: '@jiali66888', href: 'https://t.me/jiali66888' },
  ],
};

/* ------------------------------------------------------------- 事件推送(SSE) */
const sseClients = new Set();
function emit(channel, entry) {
  const payload = `event: ${channel}\ndata: ${JSON.stringify(entry)}\n\n`;
  for (const res of sseClients) {
    try { res.write(payload); } catch { sseClients.delete(res); }
  }
}

const workflowEngine = new WorkflowEngine({ emit: (event) => emit('workflow', event) });

let originalToolbox;
function getOriginalToolbox() {
  if (!originalToolbox) {
    originalToolbox = new ToolboxEngine({
      workspace: path.join(DATA_DIR, 'original-toolbox'),
      emit: (entry) => emit('original-toolbox', entry),
    });
  }
  return originalToolbox;
}

/* --------------------------------------------------- 原生对话框（替代 Electron） */
function psQuote(value) {
  return String(value).replace(/'/g, "''");
}

function runPowerShell(script) {
  return new Promise((resolve, reject) => {
    const child = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-STA', '-Command', script], {
      windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'],
    });
    let out = '';
    let err = '';
    child.stdout.on('data', (chunk) => { out += chunk.toString('utf8'); });
    child.stderr.on('data', (chunk) => { err += chunk.toString('utf8'); });
    child.on('error', reject);
    child.on('close', () => resolve({ out: out.trim(), err: err.trim() }));
  });
}

async function pickDirectory(title = '选择目录') {
  if (process.platform !== 'win32') return process.env.BREWDESK_PICK_DIR || null;
  const script = [
    'Add-Type -AssemblyName System.Windows.Forms | Out-Null',
    '$d = New-Object System.Windows.Forms.FolderBrowserDialog',
    `$d.Description = '${psQuote(title)}'`,
    '$d.ShowNewFolderButton = $true',
    'if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $d.SelectedPath }',
  ].join('\n');
  const { out } = await runPowerShell(script);
  return out ? out.split(/\r?\n/)[0] : null;
}

async function pickFile(title = '选择文件') {
  if (process.platform !== 'win32') return process.env.BREWDESK_PICK_FILE || null;
  const script = [
    'Add-Type -AssemblyName System.Windows.Forms | Out-Null',
    '$d = New-Object System.Windows.Forms.OpenFileDialog',
    `$d.Title = '${psQuote(title)}'`,
    '$d.CheckFileExists = $true',
    'if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $d.FileName }',
  ].join('\n');
  const { out } = await runPowerShell(script);
  return out ? out.split(/\r?\n/)[0] : null;
}

async function pickSavePath(defaultPath) {
  if (process.platform !== 'win32') return null;
  const script = [
    'Add-Type -AssemblyName System.Windows.Forms | Out-Null',
    '$d = New-Object System.Windows.Forms.SaveFileDialog',
    `$d.FileName = '${psQuote(path.basename(defaultPath))}'`,
    `$d.InitialDirectory = '${psQuote(path.dirname(defaultPath))}'`,
    'if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $d.FileName }',
  ].join('\n');
  const { out } = await runPowerShell(script);
  return out ? out.split(/\r?\n/)[0] : null;
}

function openPath(target) {
  return new Promise((resolve, reject) => {
    if (process.platform === 'win32') {
      const child = spawn('cmd.exe', ['/c', 'start', '', target], { windowsHide: true, detached: true, stdio: 'ignore' });
      child.on('error', reject);
      child.unref();
      return resolve(null);
    }
    const bin = process.platform === 'darwin' ? 'open' : 'xdg-open';
    const child = spawn(bin, [target], { detached: true, stdio: 'ignore' });
    child.on('error', reject);
    child.unref();
    resolve(null);
  });
}

async function openExternal(url) {
  await openPath(url);
  return url;
}

/* ------------------------------------------------------------------ 中转持久化 */
function relayConfigFile() {
  return path.join(DATA_DIR, 'relay.json');
}

function saveRelayConfig(payload) {
  if (!PERSIST_KEY) return;
  try {
    const data = {
      mode: payload.mode, baseUrl: payload.baseUrl, authToken: payload.authToken,
      wireApi: payload.wireApi, modelsPath: payload.modelsPath, usagePath: payload.usagePath,
      responsesPath: payload.responsesPath, chatCompletionsPath: payload.chatCompletionsPath,
      savedAt: new Date().toISOString(),
    };
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(relayConfigFile(), JSON.stringify(data, null, 2), { mode: 0o600 });
  } catch { /* 持久化失败不影响本次会话 */ }
}

async function restoreRelayConfig() {
  if (!PERSIST_KEY) return;
  try {
    if (!fs.existsSync(relayConfigFile())) return;
    const data = JSON.parse(fs.readFileSync(relayConfigFile(), 'utf8'));
    if (!data || data.mode === 'preview') return;
    relayAdapter.reconfigure(data);
  } catch { /* 忽略过期或损坏的本地配置 */ }
}

/* -------------------------------------------------------------------- handlers */
const handlers = Object.create(null);

handlers['coldbrew:meta'] = () => ({
  activation: ACTIVATION_WORD,
  control: CONTROL_WORD,
  title: APP_TITLE,
  profiles: PROFILES,
  seats: SEATS,
  channels: CHANNELS,
  community: COMMUNITY,
  version: workbenchCore.VERSION,
});

handlers['coldbrew:activate'] = (_ctx, payload = {}) => activate({
  word: payload.word, profile: payload.profile, channel: payload.channel, prompt: payload.prompt,
});

handlers['coldbrew:transaction'] = async (_ctx, action, payload = {}) => {
  if (action === 'gate-create') return activationGate.create(payload.seat);
  if (action === 'gate-input') return activationGate.input(payload.id, payload.text);
  if (action === 'gate-reset') { activationGate.reset(payload.id); return { ok: true }; }
  if (action === 'auto-select') {
    const found = detectDirectory(payload.seat);
    seatTransactions.select(found.root, { layout: found.layout });
    return found;
  }
  if (action === 'select') {
    const picked = payload.path || await pickDirectory('选择当前模型的配置目录（仅操作预览列出的文件）');
    if (!picked) return { canceled: true };
    const layout = payload.seat === 'deepseek'
      ? 'deepseek-harness'
      : payload.seat === 'glm53' && path.basename(picked).toLowerCase() === '.zcode' ? 'zcode' : 'default';
    return seatTransactions.select(picked, { layout });
  }
  if (action === 'preview') return seatTransactions.preview(payload.seat);
  if (action === 'file') return seatTransactions.file(payload.id, payload.index);
  if (action === 'verify') return seatTransactions.verify(payload.seat);
  if (action === 'history') return seatTransactions.history();
  if (action === 'deploy' || action === 'restore') {
    if (payload.confirm !== true) throw new Error('请先确认文件操作');
    return action === 'deploy' ? seatTransactions.deploy(payload.id) : seatTransactions.restore(payload.id);
  }
  throw new Error('未知文件操作');
};

handlers['coldbrew:relay'] = async (_ctx, action, payload = {}) => {
  if (action === 'status') return relayAdapter.status();
  if (action === 'providers') return relayAdapter.providerPresets();
  if (action === 'models') return relayAdapter.models();
  if (action === 'test') return relayAdapter.testConnection();
  if (action === 'catalog') return relayAdapter.catalog();
  if (action === 'entitlement') return relayAdapter.entitlement(payload);
  if (action === 'usage') return relayAdapter.usage(payload);
  if (action === 'preflight') return relayAdapter.preflight(payload);
  if (action === 'submit') return relayAdapter.submit(payload);
  if (action === 'configure') {
    const result = relayAdapter.reconfigure(payload);
    saveRelayConfig(payload);
    return result;
  }
  throw new Error('未知中转操作');
};

handlers['coldbrew:tools-health'] = (_ctx, payload = {}) => healthCheckTools(payload?.ids);
handlers['coldbrew:workflow-templates'] = () => workflowEngine.templates();
handlers['coldbrew:workflows'] = () => workflowEngine.templates();
handlers['coldbrew:workflow-plan'] = (_ctx, payload = {}) => planWorkflow(payload);
handlers['coldbrew:workflow-start'] = (_ctx, payload = {}) => workflowEngine.start(payload);
handlers['coldbrew:workflow-status'] = (_ctx, taskId) => workflowEngine.get(taskId);
handlers['coldbrew:workflow-list'] = () => workflowEngine.list();
handlers['coldbrew:workflow-pause'] = (_ctx, taskId) => workflowEngine.pause(taskId);
handlers['coldbrew:workflow-resume'] = (_ctx, payload = {}) => {
  const id = payload?.id || payload?.taskId || payload;
  return workflowEngine.resume(id, payload?.input || {});
};
handlers['coldbrew:workflow-cancel'] = (_ctx, taskId) => workflowEngine.cancel(taskId);
handlers['coldbrew:workflow-clear'] = (_ctx, taskId) => workflowEngine.clear(taskId);

handlers['coldbrew:ida-status'] = (_ctx, payload = {}) => idaMcp.probeIdaMcp(payload);
handlers['coldbrew:ida-call'] = (_ctx, payload = {}) => {
  const tool = payload?.tool || payload?.name;
  if (!tool) throw new Error('IDA MCP 工具名不能为空。');
  return idaMcp.callIdaMcp(tool, payload.args || payload.arguments || {}, payload);
};

handlers['coldbrew:compose'] = (_ctx, payload) => workbenchCore.compose(payload);
handlers['coldbrew:evaluate'] = (_ctx, answer, options) => workbenchCore.evaluate(answer, options);
handlers['coldbrew:inspect'] = () => seatRuntime.inspectAll();
handlers['coldbrew:gemini'] = (_ctx, verb, payload = {}) => geminiSeat.run(verb, payload.home);
handlers['coldbrew:seat'] = (_ctx, seatId, verb, payload = {}) => seatRuntime.run(String(seatId || ''), verb, payload.home);

handlers['coldbrew:toolbox'] = async (_ctx, payload = {}) => {
  const action = String(payload.action || 'status');
  if (action === 'status') return idaToolbox.status();
  if (action === 'install' || action === 'uninstall') {
    if (payload.confirm === false) return { canceled: true, ...idaToolbox.status() };
    return action === 'install' ? idaToolbox.install() : idaToolbox.uninstall();
  }
  if (action === 'reveal') {
    const current = idaToolbox.status();
    if (!current.targetExists) throw new Error('还没有插件文件夹，先装一次中文');
    const opened = await openPath(current.target);
    if (opened) throw new Error(opened);
    return current;
  }
  if (action === 'mcp-status') return idaMcp.status();
  if (action === 'mcp-install' || action === 'mcp-uninstall') {
    if (payload.confirm === false) return { canceled: true, ...idaMcp.status() };
    return action === 'mcp-install' ? idaMcp.installClients() : idaMcp.uninstallClients();
  }
  if (action === 'mcp-plugin' || action === 'mcp-plugin-uninstall') {
    if (payload.confirm === false) return { canceled: true, ...idaMcp.status() };
    if (action === 'mcp-plugin-uninstall') return idaMcp.uninstallPlugin();
    const source = await idaMcp.installPackage();
    return idaMcp.installPlugin({ pluginSource: source });
  }
  throw new Error('未知工具箱操作');
};

handlers['coldbrew:original-toolbox'] = async (_ctx, action, payload = {}) => {
  const engine = getOriginalToolbox();
  if (action === 'catalog') return engine.catalog();
  if (action === 'start') return engine.start(payload.name, payload.arguments || {});
  if (action === 'status') return engine.get(payload.id);
  if (action === 'list') return engine.list();
  if (action === 'cancel') return engine.cancel(payload.id);
  if (action === 'import') {
    const picked = await pickFile('选择要分析的样本（保留原件，复制到工具箱工作目录）');
    return picked ? engine.importSample(picked) : { canceled: true };
  }
  if (action === 'agent') {
    const input = {
      goal: String(payload.goal || '').slice(0, 8000),
      target: String(payload.target || ''),
      modelId: String(payload.modelId || ''),
      maxRounds: payload.maxRounds || 8,
      idaUrl: payload.idaUrl ? String(payload.idaUrl) : undefined,
    };
    if (!input.target) throw new Error('先填写目标或选一个样本');
    if (relayAdapter.status().mode === 'preview') throw new Error('先到中转页填写 API Key 并验证模型');
    return engine.start('ai_task', input, (ctx) => runAgent(engine, relayAdapter, input, ctx));
  }
  if (action === 'connection') {
    return {
      mcpServers: {
        'lbw-toolbox': {
          command: process.execPath,
          args: [path.join(TOOLBOX_ROOT, 'mcp.js'), '--workspace', engine.workspace],
        },
      },
    };
  }
  if (action === 'skill') return fs.readFileSync(path.join(TOOLBOX_ROOT, 'SKILL.md'), 'utf8');
  if (action === 'export-skill' || action === 'export-task') {
    const task = action === 'export-task' ? engine.get(payload.id) : null;
    const fileName = task ? `lbw-${task.id}.json` : 'lbw-toolbox-SKILL.md';
    const picked = await pickSavePath(path.join(engine.workspace, fileName));
    if (!picked) return { canceled: true };
    fs.writeFileSync(picked, task ? JSON.stringify(task, null, 2) : fs.readFileSync(path.join(TOOLBOX_ROOT, 'SKILL.md'), 'utf8'), 'utf8');
    return { file: picked };
  }
  if (action === 'report') {
    const task = engine.get(payload.id);
    if (!task.report) throw new Error('报告尚未生成');
    const target = path.join(engine.workspace, task.report.directory);
    const error = await openPath(target);
    if (error) throw new Error(error);
    return { directory: target };
  }
  throw new Error('未知原创工具箱操作');
};

handlers['coldbrew:beginner'] = async (_ctx, action, payload = {}) => {
  if (action === 'catalog' || action === 'upstream-catalog') return upstreamSkills.catalog();
  if (action === 'upstream-status') return beginner.statusOne(String(payload.seat || ''));
  if (action === 'upstream-prepare') return beginner.prepareOne(String(payload.seat || ''), { confirm: payload.confirm === true });
  if (action === 'scan') {
    const links = beginner.collectShortcuts();
    return beginner.scanAll().map((row) => ({ ...row, launchers: row.ok ? beginner.launchersFrom(row.seat, links) : [] }));
  }
  if (action === 'install') return beginner.installOne(String(payload.seat || ''), { confirm: payload.confirm === true });
  if (action === 'uninstall') return beginner.uninstallOne(String(payload.seat || ''), { confirm: payload.confirm === true });
  if (action === 'open') {
    const seat = String(payload.seat || '');
    const hit = beginner.matchLauncher(seat, payload.path);
    const opened = await openPath(hit.path);
    if (opened) throw new Error(opened);
    return { ok: true, name: hit.name };
  }
  throw new Error('未知小白操作');
};

handlers['coldbrew:open-docs'] = async () => {
  const target = path.join(ROOT, 'resources', 'public', 'docs', 'index.html');
  if (fs.existsSync(target)) {
    await openPath(target);
    return target;
  }
  const channel = 'https://t.me/lbwapi';
  await openExternal(channel);
  return channel;
};

handlers['coldbrew:open-external'] = async (_ctx, value) => {
  const url = String(value || '').trim();
  if (!/^https:\/\/(?:github\.com|(?:www\.)?lbwapishop\.online|(?:www\.)?lbwapi\.online|t\.me|telegram\.me)(\/|$)/i.test(url)) throw new Error('这个链接打不开');
  return openExternal(url);
};

handlers['window:minimize'] = () => false;
handlers['window:maximize'] = () => false;
handlers['window:close'] = () => false;

/* ---------------------------------------------------------------- HTTP 服务 */
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.map': 'application/json; charset=utf-8',
};

function send(res, status, body, headers = {}) {
  res.writeHead(status, { 'Cache-Control': 'no-store', ...headers });
  res.end(body);
}

function serveStatic(req, res, pathname) {
  const decoded = decodeURIComponent(pathname);
  const target = path.resolve(ROOT, '.' + decoded);
  const rel = path.relative(ROOT, target);
  if (rel.startsWith('..') || path.isAbsolute(rel)) return send(res, 403, 'forbidden');
  let file = target;
  try {
    if (!fs.existsSync(file)) return send(res, 404, 'not found');
    if (fs.statSync(file).isDirectory()) {
      file = path.join(file, 'index.html');
      if (!fs.existsSync(file)) return send(res, 404, 'not found');
    }
  } catch { return send(res, 404, 'not found'); }
  const ext = path.extname(file).toLowerCase();
  const type = MIME[ext] || 'application/octet-stream';
  const stream = fs.createReadStream(file);
  stream.on('error', () => send(res, 500, 'read error'));
  res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  stream.pipe(res);
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > 64 * 1024 * 1024) { reject(new Error('请求体过大')); req.destroy(); return; }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (!chunks.length) return resolve({});
      try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
      catch { reject(new Error('请求体不是有效 JSON')); }
    });
    req.on('error', reject);
  });
}

const LOG_DIR = path.join(DATA_DIR, 'logs');
function logLine(level, message) {
  const line = `[${new Date().toISOString()}] ${level} ${message}\n`;
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const file = path.join(LOG_DIR, `server-${new Date().toISOString().slice(0, 10)}.log`);
    fs.appendFileSync(file, line, 'utf8');
  } catch { /* 日志失败不影响主流程 */ }
}

const startedAt = Date.now();

async function handleRequest(req, res) {
  const parsed = new URL(req.url, `http://127.0.0.1:${PORT}`);
  const pathname = parsed.pathname;

  if (pathname === '/api/invoke') {
    if (req.method !== 'POST') return send(res, 405, 'method not allowed');
    // CSRF 防护：只接受同源出来的 JSON POST；跨源请求会先发预检，这里一律拒绝。
    const origin = req.headers.origin;
    if (origin && origin !== `http://127.0.0.1:${PORT}` && origin !== `http://localhost:${PORT}`) {
      return send(res, 403, JSON.stringify({ ok: false, error: '拒绝跨源调用' }), { 'Content-Type': 'application/json' });
    }
    if (!String(req.headers['content-type'] || '').includes('application/json')) {
      return send(res, 415, JSON.stringify({ ok: false, error: '需要 application/json' }), { 'Content-Type': 'application/json' });
    }
    let body;
    try { body = await readJson(req); }
    catch (error) { return send(res, 400, JSON.stringify({ ok: false, error: error.message }), { 'Content-Type': 'application/json' }); }
    const { channel, args = [] } = body;
    const handler = handlers[channel];
    if (!handler) {
      return send(res, 404, JSON.stringify({ ok: false, error: `未知接口：${channel}` }), { 'Content-Type': 'application/json' });
    }
    try {
      const result = await handler({ channel }, ...args);
      return send(res, 200, JSON.stringify({ ok: true, result: result === undefined ? null : result }), { 'Content-Type': 'application/json' });
    } catch (error) {
      return send(res, 200, JSON.stringify({ ok: false, error: error && error.message ? error.message : String(error) }), { 'Content-Type': 'application/json' });
    }
  }

  if (pathname === '/api/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-store',
      Connection: 'keep-alive',
    });
    res.write(': connected\n\n');
    sseClients.add(res);
    const keep = setInterval(() => { try { res.write(': ping\n\n'); } catch { /* ignore */ } }, 20000);
    req.on('close', () => { clearInterval(keep); sseClients.delete(res); });
    return;
  }

  if (pathname === '/api/diagnostics') {
    const report = {
      ok: true,
      product: 'LBW 破甲工作台',
      version: workbenchCore.VERSION,
      node: process.version,
      platform: `${process.platform} ${process.arch}`,
      port: activePort,
      dataDir: DATA_DIR,
      uptimeMinutes: Math.round((Date.now() - startedAt) / 60000),
      persistedRelayConfig: PERSIST_KEY,
      relayMode: (() => { try { return relayAdapter.status().mode; } catch { return 'unknown'; } })(),
      upstream: (() => {
        try {
          const c = upstreamSkills.catalog();
          return { present: true, skills: c.skillCount, files: c.fileCount };
        } catch (error) { return { present: false, error: error.message }; }
      })(),
      seats: (() => {
        try {
          const rows = beginner.scanAll();
          return {
            total: rows.length,
            found: rows.filter((row) => row.ok && row.exists).map((row) => row.seat),
            missing: rows.filter((row) => !row.ok || !row.exists).map((row) => row.seat),
          };
        } catch (error) { return { total: 0, error: error.message }; }
      })(),
      writable: (() => {
        try {
          fs.mkdirSync(DATA_DIR, { recursive: true });
          const probe = path.join(DATA_DIR, `.probe-${Date.now()}`);
          fs.writeFileSync(probe, 'ok');
          fs.unlinkSync(probe);
          return true;
        } catch { return false; }
      })(),
    };
    return send(res, 200, JSON.stringify(report, null, 2), { 'Content-Type': 'application/json; charset=utf-8' });
  }

  if (pathname === '/api/health') {
    return send(res, 200, JSON.stringify({
      ok: true, product: 'brewdesk', version: workbenchCore.VERSION,
      node: process.version, platform: process.platform, port: activePort, uptimeMs: Date.now() - startedAt,
      persisted: PERSIST_KEY, dataDir: DATA_DIR,
    }), { 'Content-Type': 'application/json' });
  }

  if (pathname === '/') {
    res.writeHead(302, { Location: '/src/workbench/index.html' });
    return res.end();
  }

  if (pathname === '/favicon.ico') {
    const icon = path.join(ROOT, 'assets', 'logo.ico');
    if (fs.existsSync(icon)) {
      res.writeHead(200, { 'Content-Type': 'image/x-icon', 'Cache-Control': 'no-store' });
      return fs.createReadStream(icon).pipe(res);
    }
    return send(res, 204, '');
  }

  if (req.method === 'OPTIONS') return send(res, 403, 'cors disabled');
  if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'method not allowed');
  return serveStatic(req, res, pathname);
}

/*
 * 同时监听 IPv4 与 IPv6 回环。
 * 只绑 127.0.0.1 时，浏览器把 localhost 解析成 ::1 就会「连接被拒绝」，
 * 这是本地服务最常见的「明明在跑却打不开」。
 */
async function main() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  await restoreRelayConfig();

  const hosts = ['127.0.0.1', '::1'];
  const candidates = Array.from({ length: 10 }, (_, i) => PORT + i);
  let bound = null;
  let servers = [];

  for (const candidate of candidates) {
    const failures = [];
    const current = hosts.map((host) => {
      const instance = http.createServer(handleRequest);
      instance.on('error', (error) => { failures.push(`${host}: ${error.code || error.message}`); });
      return instance;
    });
    for (let i = 0; i < hosts.length; i += 1) {
      await new Promise((resolve) => {
        const done = () => resolve();
        current[i].once('error', done);
        current[i].listen(candidate, hosts[i], done);
      });
    }
    if (current.some((instance) => instance.listening)) {
      bound = candidate;
      servers = current;
      break;
    }
    for (const instance of current) { try { instance.close(); } catch { /* ignore */ } }
    if (candidates.indexOf(candidate) === 0) {
      logLine('WARN', `端口 ${candidate} 不可用（${failures.join('；')}），尝试下一个`);
    }
  }

  if (!bound) {
    logLine('ERROR', `端口 ${PORT}-${PORT + 9} 全部无法监听`);
    throw new Error(`端口 ${PORT}-${PORT + 9} 都无法监听。可能被其他程序占用，或安全软件拦截。可以手动换端口：set BREWDESK_PORT=8899 && node server.js`);
  }

  activePort = bound;
  if (bound !== PORT) console.log(`  （端口 ${PORT} 被占用，已自动改用 ${bound}）`);

  const url = `http://127.0.0.1:${bound}/src/workbench/index.html`;
  console.log('');
  console.log(`  LBW 破甲工作台 · 本地版 ${workbenchCore.VERSION}`);
  console.log(`  控制台: ${url}`);
  console.log(`  数据目录: ${DATA_DIR}`);
  console.log(`  监听: ${hosts.filter((host, i) => servers[i].listening).join('  +  ')}  端口 ${bound}`);
  if (PERSIST_KEY) console.log('  中转配置: 已开启本地持久化 (relay.json, 0600)');
  console.log(`  自检:   http://127.0.0.1:${bound}/api/diagnostics`);
  console.log('');
  logLine('INFO', `启动成功 port=${bound} node=${process.version}`);
  if (process.argv.includes('--open')) openPath(url).catch(() => {});
}

process.on('uncaughtException', (error) => { logLine('FATAL', error.stack || String(error)); console.error(error); });
process.on('unhandledRejection', (reason) => { logLine('ERROR', String(reason)); });

main().catch((error) => {
  logLine('FATAL', error.stack || String(error));
  console.error('启动失败:', error);
  process.exitCode = 1;
});
