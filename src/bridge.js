'use strict';
/*
 * bridge.js — 把原版 preload.js 的 window.coldbrew 映射到本地 HTTP。
 *
 * 原版 preload.js 逐个 ipcRenderer.invoke("coldbrew:xxx", ...)，这里换成
 * POST /api/invoke {channel, args}。方法名、参数顺序、返回值形状保持一致，
 * 因此 src/workbench/* 的原 UI 代码不需要改动。
 *
 * 唯一差异：Electron 的 ipcRenderer.on 事件改成 EventSource(/api/events)。
 */
(function () {
  const pending = new Map();
  let seq = 0;

  async function invoke(channel, ...args) {
    const response = await fetch('/api/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel, args }),
    });
    let data;
    try { data = await response.json(); }
    catch { throw new Error(`接口 ${channel} 返回了非 JSON 响应`); }
    if (!data.ok) throw new Error(data.error || '调用失败');
    return data.result;
  }

  const listeners = { workflow: new Set(), 'original-toolbox': new Set() };
  function subscribe(kind, fn) {
    listeners[kind].add(fn);
    return () => listeners[kind].delete(fn);
  }

  function connectEvents() {
    if (typeof EventSource === 'undefined') return;
    const source = new EventSource('/api/events');
    source.addEventListener('workflow', (event) => {
      try {
        const entry = JSON.parse(event.data);
        for (const fn of listeners.workflow) { try { fn(entry); } catch (error) { console.error(error); } }
      } catch { /* ignore */ }
    });
    source.addEventListener('original-toolbox', (event) => {
      try {
        const entry = JSON.parse(event.data);
        for (const fn of listeners['original-toolbox']) { try { fn(entry); } catch (error) { console.error(error); } }
      } catch { /* ignore */ }
    });
    source.onerror = () => {
      // EventSource 会自行重连；页面卸载时不要再重试。
      if (source.readyState === EventSource.CLOSED) setTimeout(connectEvents, 2000);
    };
  }

  const api = {
    platform: (navigator.platform || '').toLowerCase().includes('win') ? 'win32' : 'linux',
    transaction: (action, payload) => invoke('coldbrew:transaction', action, payload),
    beginner: (action, payload) => invoke('coldbrew:beginner', action, payload),
    upstream: Object.freeze({
      catalog: () => invoke('coldbrew:beginner', 'catalog'),
      status: (seat) => invoke('coldbrew:beginner', 'upstream-status', { seat }),
      prepare: (seat, confirm) => invoke('coldbrew:beginner', 'upstream-prepare', { seat, confirm: confirm === true }),
    }),
    relay: (action, payload) => invoke('coldbrew:relay', action, payload),
    compose: (payload) => invoke('coldbrew:compose', payload),
    evaluate: (answer, options) => invoke('coldbrew:evaluate', answer, options),
    meta: () => invoke('coldbrew:meta'),
    activate: (payload) => invoke('coldbrew:activate', payload),
    inspect: () => invoke('coldbrew:inspect'),
    gemini: (verb, payload) => invoke('coldbrew:gemini', verb, payload),
    seat: (seatId, verb, payload) => invoke('coldbrew:seat', seatId, verb, payload),
    toolbox: (payload) => invoke('coldbrew:toolbox', payload),
    originalToolbox: (action, payload) => invoke('coldbrew:original-toolbox', action, payload),
    onOriginalToolbox: (fn) => subscribe('original-toolbox', fn),
    toolsHealth: (payload) => invoke('coldbrew:tools-health', payload),
    workflowTemplates: () => invoke('coldbrew:workflow-templates'),
    workflows: () => invoke('coldbrew:workflows'),
    workflowPlan: (payload) => invoke('coldbrew:workflow-plan', payload),
    workflowStart: (payload) => invoke('coldbrew:workflow-start', payload),
    startWorkflow: (payload) => invoke('coldbrew:workflow-start', payload),
    workflowStatus: (taskId) => invoke('coldbrew:workflow-status', taskId),
    getWorkflow: (taskId) => invoke('coldbrew:workflow-status', taskId),
    workflowList: () => invoke('coldbrew:workflow-list'),
    workflowPause: (taskId) => invoke('coldbrew:workflow-pause', taskId),
    workflowResume: (taskId, input) => invoke('coldbrew:workflow-resume', { id: taskId, input }),
    workflowCancel: (taskId) => invoke('coldbrew:workflow-cancel', taskId),
    cancelWorkflow: (taskId) => invoke('coldbrew:workflow-cancel', taskId),
    workflowClear: (taskId) => invoke('coldbrew:workflow-clear', taskId),
    idaStatus: (payload) => invoke('coldbrew:ida-status', payload),
    idaCall: (payload) => invoke('coldbrew:ida-call', payload),
    onWorkflow: (fn) => subscribe('workflow', fn),
    onWorkflowEvent: (fn) => subscribe('workflow', fn),
    openDocs: () => invoke('coldbrew:open-docs'),
    openExternal: (url) => invoke('coldbrew:open-external', url),
    minimize: () => Promise.resolve(false),
    maximize: () => Promise.resolve(false),
    close: () => { window.close(); return Promise.resolve(false); },
  };

  Object.defineProperty(window, 'coldbrew', { value: api, writable: false, configurable: false });

  connectEvents();

  // 浏览器里没有 Electron 的自绘标题栏按钮，隐藏它们并补一个标签。
  window.addEventListener('DOMContentLoaded', () => {
    const actions = document.querySelector('.window-actions');
    if (actions) actions.style.display = 'none';
    const state = document.getElementById('environment');
    if (state && !state.dataset.bridge) {
      state.dataset.bridge = '1';
      state.title = '本地复刻版：浏览器 / Node 服务模式';
    }
  });
})();
