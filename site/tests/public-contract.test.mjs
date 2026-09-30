import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { runInNewContext } from 'node:vm';
import test from 'node:test';

const root = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(join(root, 'package.json'));
const ts = require('typescript');
const read = (path) => readFileSync(join(root, path), 'utf8');
const compiled = ts.transpileModule(read('lib/release.ts'), { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const release = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

test('published install identity stays separate from the source candidate', () => {
  assert.equal(release.CANDIDATE_VERSION, '0.3.0');
  assert.equal(release.PUBLISHED_VERSION, '0.2.2');
  assert.equal(release.INSTALL_COMMAND, 'pip install heartland-synthetic==0.2.2');
  assert.match(read('../pyproject.toml'), /version = "0\.3\.0"/);
  assert.match(read('app/page.tsx'), /Three versions, three different artifacts/);
});

test('public copy avoids unsupported exclusivity, validation and regulatory claims', () => {
  for (const path of ['app/page.tsx', 'app/layout.tsx', 'app/dataset/page.tsx', 'components/landing/hero.tsx', 'components/landing/abstract.tsx', 'components/landing/features.tsx', 'components/landing/evidence.tsx']) {
    assert.doesNotMatch(read(path), /clinically.realistic|Synthea.{0,35}(leaves|model)|1:1 port|calibrated from|Not a medical device|no PHI, by design|passing tests/i, path);
  }
  assert.match(release.SYNTHETIC_BOUNDARY, /Do not supply real patient/);
  assert.match(release.SYNTHETIC_BOUNDARY, /pending validation/);
});

test('download is the original benchmark with stable provenance', () => {
  assert.equal(createHash('sha256').update(readFileSync(join(root, 'public/data/heartland-synthetic-cohort-1000-seed42.csv'))).digest('hex'), '8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e');
  assert.match(read('app/dataset/page.tsx'), /version: "1\.0\.0"/);
  assert.match(read('app/dataset/page.tsx'), /generator v0\.2\.2 provenance/);
});

// Narrow handler tests using the actual transpiled component with hook stubs.
// These check async success/failure state, not React rendering or browser clipboard permissions.
function copyHarness(clipboard) {
  const states = [], cleanups = [], timerCalls = [];
  const source = ts.transpileModule(read('components/landing/install-command.tsx'), { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS } }).outputText;
  const module = { exports: {} };
  const context = { module, exports: module.exports, navigator: { clipboard },
    setTimeout: (fn) => { timerCalls.push(fn); return 1; }, clearTimeout: () => {},
    require: (name) => {
      if (name === 'react') return {
        useState: (value) => { const n = states.length; states.push(value); return [value, (next) => { states[n] = next; }]; },
        useRef: (value) => ({ current: value }),
        useEffect: (fn) => cleanups.push(fn()),
      };
      if (name === '@/lib/release') return release;
      return require(name);
    },
  };
  runInNewContext(source, context);
  const tree = module.exports.InstallCommand();
  function findButton(node) {
    if (!node || typeof node !== 'object') return null;
    if (node.type === 'button') return node;
    for (const child of [node.props?.children].flat(Infinity)) {
      const found = findButton(child); if (found) return found;
    }
    return null;
  }
  const button = findButton(tree);
  assert.ok(button);
  return { click: button.props.onClick, states, cleanups, timerCalls };
}

test('copy confirms only a resolved write of the exact pinned command', async () => {
  let written;
  const harness = copyHarness({ writeText: async (text) => { written = text; } });
  await harness.click();
  assert.equal(written, release.INSTALL_COMMAND);
  assert.deepEqual(harness.states, [true, false, false]);
  assert.equal(harness.timerCalls.length, 1);
  harness.timerCalls[0]();
  assert.equal(harness.states[0], false);
});

test('copy failure or unavailable clipboard does not report success', async () => {
  for (const clipboard of [undefined, { writeText: async () => { throw new Error('denied'); } }]) {
    const harness = copyHarness(clipboard);
    await harness.click();
    assert.deepEqual(harness.states, [false, true, false]);
    assert.equal(harness.timerCalls.length, 0);
  }
  assert.match(read('components/landing/install-command.tsx'), /Select the command above and copy it manually/);
  assert.doesNotMatch(read('components/landing/install-command.tsx'), /execCommand|truncate/);
});

test('code samples offer keyboard scroll regions', () => {
  assert.match(read('components/landing/install.tsx'), /tabIndex=\{0\} role="region"/);
});

// These assertions intentionally require a fresh production build; absent/stale HTML is not a skip.
test('built home includes the candidate boundary, published pin and all three artifact labels', () => {
  const html = read('out/index.html');
  const text = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ');
  for (const expected of ['Published package', 'Source candidate', 'Preserved benchmark', release.INSTALL_COMMAND, 'pending validation', 'Copy command']) {
    assert.ok(text.includes(expected), `Missing rendered text: ${expected}`);
  }
  assert.doesNotMatch(text, /clinically.realistic|Not a medical device|no PHI, by design/i);
  assert.match(html, /href="\/dataset\/"/);
});

test('built dataset structured metadata keeps original identity and CSV hash', () => {
  const html = read('out/dataset/index.html');
  const json = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  assert.ok(json, 'Dataset JSON-LD must exist');
  const dataset = JSON.parse(json[1]);
  assert.equal(dataset.version, '1.0.0');
  assert.equal(dataset.distribution[0].sha256, '8fbce909272274129f94db2b80b179b493e64fbc382a88515a851089b2edda8e');
  assert.match(dataset.description, /heartland-synthetic v0\.2\.2/);
  assert.match(dataset.description, /fixed outcome settings cannot validate/);
  assert.equal(createHash('sha256').update(readFileSync(join(root, 'out/data/heartland-synthetic-cohort-1000-seed42.csv'))).digest('hex'), dataset.distribution[0].sha256);
});
