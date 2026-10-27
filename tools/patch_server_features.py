"""给 server.js 补三个交付必需的能力：

1. 端口自动避让：8788 被占用时自动试 8789..8797，不再一启动就报错退出
2. /api/diagnostics：一条 URL 给出全部排障信息，客服让客户打开截图即可
3. 日志落盘：启动与异常写入 ~/.brewdesk/logs/server-YYYY-MM-DD.log

改完会做一次语法检查。
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "server.js"
src = P.read_text(encoding="utf-8")

# ---------------------------------------------------------------- 1. 日志目录
if "function logLine(" not in src:
    anchor = "const startedAt = Date.now();"
    assert anchor in src, "startedAt 锚点缺失"
    logger = '''const LOG_DIR = path.join(DATA_DIR, 'logs');
function logLine(level, message) {
  const line = `[${new Date().toISOString()}] ${level} ${message}\\n`;
  try {
    fs.mkdirSync(LOG_DIR, { recursive: true });
    const file = path.join(LOG_DIR, `server-${new Date().toISOString().slice(0, 10)}.log`);
    fs.appendFileSync(file, line, 'utf8');
  } catch { /* 日志失败不影响主流程 */ }
}

const startedAt = Date.now();'''
    src = src.replace(anchor, logger, 1)

# ---------------------------------------------------------------- 2. 自检接口
if "/api/diagnostics" not in src:
    anchor = "  if (pathname === '/api/health') {"
    assert anchor in src
    diag = '''  if (pathname === '/api/diagnostics') {
    const report = {
      ok: true,
      product: 'LBW 破甲工作台',
      version: workbenchCore.VERSION,
      node: process.version,
      platform: `${process.platform} ${process.arch}`,
      port: PORT,
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

  if (pathname === '/api/health') {'''
    src = src.replace(anchor, diag, 1)

# ------------------------------------------------------- 3. 端口避让 + 启动日志
start = src.index("async function main() {")
end = src.index("main().catch(")
new_main = '''async function main() {
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

'''
src = src[:start] + new_main + src[end:]

# 全局未捕获异常也落盘
if "process.on('uncaughtException'" not in src:
    src = src.replace(
        "main().catch((error) => {",
        "process.on('uncaughtException', (error) => { logLine('FATAL', error.stack || String(error)); console.error(error); });\n"
        "process.on('unhandledRejection', (reason) => { logLine('ERROR', String(reason)); });\n\n"
        "main().catch((error) => {\n  logLine('FATAL', error.stack || String(error));",
        1,
    )

P.write_text(src, encoding="utf-8")
print("server.js 已更新")

check = subprocess.run([sys.executable, "-c",
                        "import ast,sys;ast.parse(open(r'%s',encoding='utf-8').read())" % P])
print("syntax:", "OK" if check.returncode == 0 else "FAIL")
