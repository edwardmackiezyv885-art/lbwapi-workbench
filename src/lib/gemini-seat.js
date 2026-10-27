const { renderPack, markers } = require("./seat-packs");
const runtime = require("./seat-runtime");

const { begin: MARKER_BEGIN, end: MARKER_END } = markers("gemini");

function packText() {
  return renderPack("gemini");
}

function resolveHome(home) {
  return home || runtime.seatHomes().gemini;
}

function preview(home) {
  return runtime.preview("gemini", home);
}

function deploy(home) {
  return runtime.deploy("gemini", home);
}

function verify(home) {
  return runtime.verify("gemini", home);
}

function restore(home) {
  return runtime.restore("gemini", home);
}

function run(verb, home) {
  return runtime.run("gemini", verb, home);
}

module.exports = { resolveHome, packText, preview, deploy, verify, restore, run, MARKER_BEGIN, MARKER_END };
