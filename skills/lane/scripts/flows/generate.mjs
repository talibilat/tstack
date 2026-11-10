// Smart Syllabus content through the real UI: upload a learning asset -> real parse (shared doc-parser) ->
// Full AI Gen -> wait for the run -> approve the review -> publish validation -> publish.
// Every step saves a numbered screenshot and one log line in the proof folder.
//
// Usage: lane flow <N> generate --syllabus <versionId> --pdf <file.pdf> [--as <email>] [--from <step>] [--until <step>]
// The `foundation` flow prints the syllabus id it created.
import { appendFileSync, mkdirSync } from 'node:fs';
import { basename, join } from 'node:path';
import { openLane } from '../browser.mjs';

const args = Object.fromEntries(
	process.argv.slice(2).reduce((acc, cur, i, all) => (cur.startsWith('--') ? [...acc, [cur.slice(2), all[i + 1]]] : acc), []),
);
const SYL = args.syllabus ?? (() => { throw new Error('--syllabus is required'); })();
const PDF = args.pdf;
const AS = args.as ?? 'e2e-professor@example.com';
const PROOF = process.env.PROOF_DIR;
mkdirSync(PROOF, { recursive: true });
const LOG = join(PROOF, 'steps.log');
let skipping = Boolean(args.from);
let stepNo = 0;
const t0 = Date.now();
const { page, goto, close } = await openLane({ as: AS });
const tid = (id) => page.getByTestId(id);
const state = { assetId: args.asset, runId: args.run };

function log(line) {
	const msg = `[${new Date().toISOString()}] +${Math.round((Date.now() - t0) / 1000)}s ${line}`;
	console.log(msg);
	appendFileSync(LOG, msg + '\n');
}
async function shot(name) {
	const file = join(PROOF, `${String(stepNo).padStart(2, '0')}-${name}.png`);
	await page.screenshot({ path: file, fullPage: true });
	return file;
}
async function describe() {
	return page.evaluate(() => ({
		url: location.pathname,
		dialog: (document.querySelector('[role=dialog]')?.innerText ?? '').replace(/\s+/g, ' ').slice(0, 600),
		testids: [...new Set([...document.querySelectorAll('[data-testid]')].filter((e) => e.offsetParent).map((e) => e.dataset.testid))].slice(0, 80),
		buttons: [...new Set([...document.querySelectorAll('button')].filter((b) => b.offsetParent).map((b) => `${b.innerText.trim().slice(0, 40)}${b.disabled ? ' (disabled)' : ''}`).filter(Boolean))].slice(0, 60),
	}));
}
async function step(name, fn) {
	stepNo += 1;
	if (skipping) {
		if (name !== args.from) { log(`STEP ${stepNo} ${name} skipped (--from ${args.from})`); return; }
		skipping = false;
	}
	log(`STEP ${stepNo} ${name} ...`);
	try {
		const note = await fn();
		const file = await shot(name);
		log(`STEP ${stepNo} ${name} OK${note ? ` (${note})` : ''} -> ${basename(file)}`);
	} catch (err) {
		const file = await shot(`${name}-FAILED`).catch(() => '(no screenshot)');
		log(`STEP ${stepNo} ${name} FAILED: ${err.message.split('\n')[0]} -> ${basename(String(file))}`);
		log(`  page state: ${JSON.stringify(await describe().catch(() => ({})))}`);
		await close();
		process.exit(1);
	}
	if (args.until === name) { log(`stopping after ${name} (--until)`); await close(); process.exit(0); }
}
async function api(path) {
	const r = await page.request.get(`/api${path}`);
	if (!r.ok()) throw new Error(`GET /api${path} -> ${r.status()}`);
	return r.json();
}

await step('upload-asset', async () => {
	if (!PDF) throw new Error('--pdf is required');
	await goto(`/syllabus/${SYL}/assets`);
	await tid('asset-list-open-upload-modal').click();
	await tid('create-asset-title').fill(`lane ${basename(PDF, '.pdf')}`);
	await tid('create-asset-file-input').setInputFiles(PDF);
	const created = page.waitForResponse((r) => r.request().method() === 'POST' && /learning-assets/.test(r.url()) && r.ok(), { timeout: 120_000 });
	await page.getByRole('button', { name: 'Add to syllabus' }).click();
	const res = await created;
	const body = await res.json().catch(() => ({}));
	state.assetId = body.id ?? body.assetId ?? body.learningAssetId;
	await page.getByRole('dialog').waitFor({ state: 'hidden', timeout: 180_000 });
	return `asset ${state.assetId ?? '(id from list)'}`;
});

await step('wait-asset-parse', async () => {
	// The asset goes through the real doc-parser in the base stack. Poll the same endpoint the app uses.
	if (!state.assetId) {
		const list = await api(`/smart-syllabus/learning-assets?syllabusVersionId=${SYL}`);
		const items = Array.isArray(list) ? list : list.data ?? list.items ?? [];
		state.assetId = items[0]?.id;
	}
	if (!state.assetId) throw new Error('could not find the uploaded asset');
	const deadline = Date.now() + 20 * 60_000;
	let last = '';
	while (Date.now() < deadline) {
		const s = await api(`/smart-syllabus/learning-assets/${state.assetId}/parse-status`).catch((e) => ({ parseStatus: `error ${e.message}` }));
		if (s.parseStatus !== last) { log(`  parse status: ${s.parseStatus}`); last = s.parseStatus; }
		if (s.parseStatus === 'completed') {
			const pending = await api(`/ai/generate/pending-assets?syllabusVersionId=${SYL}`).catch(() => ({ pendingCount: 0 }));
			if (!pending.pendingCount) return `asset ${state.assetId} parsed`;
		}
		if (s.parseStatus === 'failed') throw new Error(`asset parse failed: ${s.parseError ?? 'unknown'}`);
		await page.waitForTimeout(10_000);
	}
	throw new Error('asset parse did not finish in 20 minutes');
});

await step('open-full-ai-gen', async () => {
	await goto(`/syllabus/${SYL}/assets`);
	// Indexing (embeddings) runs after the parse. A failed asset keeps Full AI Gen disabled.
	if (await page.locator('[data-testid^="processing-status-badge-failed"]').first().isVisible({ timeout: 3000 }).catch(() => false)) {
		throw new Error('the asset failed indexing, so Full AI Gen is disabled; check `lane logs N ai-backend` (an invalid GOOGLE_API_KEY causes this)');
	}
	await tid('editor-sidebar-full-ai-gen').click();
	await page.getByRole('dialog').first().waitFor();
	await page.waitForTimeout(3000);
	log(`  dialog: ${JSON.stringify(await describe())}`);
});

log('DONE');
await close();
