// Golden path through the real UI: course -> New Version -> Course Foundation -> upload a PDF -> real parse ->
// extract -> review (accept all) -> validate -> approve -> create Smart Syllabus -> validate -> publish.
// Every step saves a numbered screenshot and one log line in the proof folder.
//
// Usage: lane flow <N> foundation --pdf <file.pdf> [--course <courseId>] [--as <email>] [--until <step>]
// Env from `lane flow`: LANE_FE, LANE_DIR, LANE_SCRIPTS, PROOF_DIR.
import { appendFileSync, mkdirSync } from 'node:fs';
import { basename, join } from 'node:path';
import { openLane } from '../browser.mjs';

const args = Object.fromEntries(
	process.argv.slice(2).reduce((acc, cur, i, all) => (cur.startsWith('--') ? [...acc, [cur.slice(2), all[i + 1]]] : acc), []),
);
const PDF = args.pdf ?? (() => { throw new Error('--pdf is required'); })();
const AS = args.as ?? 'e2e-professor@example.com';
const COURSE = args.course; // default: first course with zero syllabus versions
const UNTIL = args.until;
// --from <step> --course <id> resumes an earlier run: earlier steps are skipped and the flow opens the
// course's foundation wizard (or, for publish steps, needs --syllabus <id>).
const FROM = args.from;
let skipping = Boolean(FROM);
// --reject '<regex>': the operator's decision, never the flow's. Before accepting, every Assessment
// candidate with a line matching it is rejected through the app's Reject button. Use it after reading
// a FINDING that names duplicate or roll-up components (see the flow's step log from an earlier run).
// Case-insensitive: card text comes back as displayed, and the app upper-cases titles with CSS.
const REJECT = args.reject ? new RegExp(args.reject, 'i') : null;
const PROOF = process.env.PROOF_DIR;
mkdirSync(PROOF, { recursive: true });
const LOG = join(PROOF, 'steps.log');

let stepNo = 0;
const t0 = Date.now();
const { page, goto, close } = await openLane({ as: AS });
const tid = (id) => page.getByTestId(id);

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
	return page.evaluate(() => {
		const ids = [...document.querySelectorAll('[data-testid]')]
			.filter((e) => e.offsetParent !== null)
			.map((e) => e.getAttribute('data-testid'));
		const buttons = [...document.querySelectorAll('button')]
			.filter((b) => b.offsetParent !== null)
			.map((b) => `${b.innerText.trim().slice(0, 40)}${b.disabled ? ' (disabled)' : ''}`)
			.filter(Boolean);
		return { url: location.pathname, testids: [...new Set(ids)].slice(0, 80), buttons: [...new Set(buttons)].slice(0, 60) };
	});
}

async function step(name, fn) {
	stepNo += 1;
	if (skipping) {
		if (name !== FROM) { log(`STEP ${stepNo} ${name} skipped (--from ${FROM})`); return; }
		skipping = false;
		if (!['open-course', 'choose-foundation'].includes(name) && !state.syllabusId) {
			if (!state.courseId) throw new Error('--from needs --course');
			await goto(`/professor/courses/${state.courseId}/course-foundation`);
			await tid('course-foundation-wizard').waitFor({ timeout: 60_000 });
			// The wizard opens on the step that matches the foundation's state; go to the one we resume.
			const tab = { 'add-source': 'sources', 'wait-for-parse': 'sources', extract: 'sources', summary: 'summary',
				'review-accept-all': 'review', 'validate-foundation': 'validate', 'approve-foundation': 'approve',
				'create-smart-syllabus': 'approve' }[name];
			if (tab) await tid(`foundation-step-tab-${tab}`).click().catch(() => {});
		}
	}
	log(`STEP ${stepNo} ${name} ...`);
	try {
		const note = await fn();
		const file = await shot(name);
		log(`STEP ${stepNo} ${name} OK${note ? ` (${note})` : ''} -> ${basename(file)}`);
	} catch (err) {
		const file = await shot(`${name}-FAILED`).catch(() => '(no screenshot)');
		const state = await describe().catch(() => ({}));
		log(`STEP ${stepNo} ${name} FAILED: ${err.message.split('\n')[0]} -> ${basename(String(file))}`);
		log(`  page state: ${JSON.stringify(state)}`);
		await close();
		process.exit(1);
	}
	if (UNTIL && name === UNTIL) {
		log(`stopping after ${name} (--until)`);
		await close();
		process.exit(0);
	}
}

async function api(path) {
	const r = await page.request.get(`/api${path}`);
	if (!r.ok()) throw new Error(`GET /api${path} -> ${r.status()}`);
	return r.json();
}

const state = { courseId: COURSE, syllabusId: args.syllabus };

await step('open-course', async () => {
	if (!state.courseId) {
		const mine = await api('/courses/my-courses');
		const list = Array.isArray(mine) ? mine : mine.data ?? mine.items ?? [];
		for (const c of list) {
			const v = await api(`/smart-syllabus/versions?courseId=${c.id}&take=1`);
			const total = v.total ?? (Array.isArray(v) ? v.length : (v.data ?? []).length);
			let foundation = true;
			const f = await page.request.get(`/api/course-foundation/by-course/${c.id}`);
			if (f.status() === 404) foundation = false;
			if (total === 0 && !foundation) { state.courseId = c.id; break; }
		}
		if (!state.courseId) throw new Error('no course without syllabus versions and foundation; pass --course');
	}
	await goto(`/professor/courses/${state.courseId}`);
	await page.getByRole('heading', { name: 'Syllabus Versions' }).waitFor({ timeout: 30_000 });
	return `course ${state.courseId}`;
});

await step('choose-foundation', async () => {
	await page.getByRole('button', { name: 'New Version' }).click();
	await page.getByRole('dialog', { name: 'Create New Syllabus Version' }).waitFor();
	await page.getByRole('button', { name: /Open Course Foundation/ }).click();
	// A short form names the new version before the wizard opens.
	await tid('syllabus-form-modal').waitFor({ timeout: 30_000 });
	await tid('syllabus-form-title-input').fill(`lane foundation ${new Date().toISOString().slice(0, 16)}`);
	await tid('syllabus-form-description-input').fill('Created by the lane golden-path flow from a real PDF upload.');
	await page.getByRole('button', { name: 'Continue to Course Foundation' }).click();
	await page.waitForURL(/course-foundation/, { timeout: 60_000 });
	const start = tid('foundation-start-revision');
	await Promise.race([tid('course-foundation-wizard').waitFor({ timeout: 60_000 }), start.waitFor({ timeout: 60_000 })]);
	if (await start.isVisible().catch(() => false)) await start.click();
	await tid('foundation-sources-step').waitFor({ timeout: 60_000 });
});

await step('add-source', async () => {
	await tid('foundation-add-source-open').click();
	await tid('add-source-modal').waitFor();
	await tid('add-source-type').click();
	await page.getByRole('option', { name: 'Course Handbook' }).click();
	await tid('add-source-title').fill(`lane ${basename(PDF, '.pdf')}`);
	await tid('add-source-file-input').setInputFiles(PDF);
	await tid('add-source-submit').click();
	await tid('add-source-modal').waitFor({ state: 'hidden', timeout: 120_000 });
	await tid('foundation-sources-list').waitFor({ timeout: 30_000 });
	return basename(PDF);
});

await step('wait-for-parse', async () => {
	// The real doc-parser runs; the source row shows its processing state. Reload until it is processed.
	const deadline = Date.now() + 20 * 60_000;
	let last = '';
	while (Date.now() < deadline) {
		const text = await tid('foundation-sources-list').innerText().catch(() => '');
		// Badge words only; "Uploaded documents" is a heading in the same list.
		const status = (text.match(/\b(uploaded(?! documents)|pending|processing|processed|failed|error|ready)\b/gi) ?? []).join(',').toLowerCase();
		if (status !== last) { log(`  source status: ${status || '(none shown)'}`); last = status; }
		if (/failed|error/.test(status)) throw new Error(`source processing failed: ${status}`);
		if (/processed|ready/.test(status) && !/processing|uploaded/.test(status)) return status;
		await page.waitForTimeout(15_000);
		await page.reload({ waitUntil: 'domcontentloaded' });
		await tid('course-foundation-wizard').waitFor({ timeout: 60_000 });
		await tid('foundation-step-tab-sources').click().catch(() => {});
		await tid('foundation-sources-list').waitFor({ timeout: 30_000 });
	}
	throw new Error('parse did not finish in 20 minutes');
});

await step('extract', async () => {
	await tid('foundation-sources-continue').click();
	await tid('foundation-extract-confirm-confirm').click();
	// Extraction runs as a background job (about 5-10 minutes for a small handbook). The page polls, but a
	// failed poll leaves "Something went wrong" on screen until reload, so reload every minute like a user.
	const deadline = Date.now() + 25 * 60_000;
	let reloads = 0;
	while (Date.now() < deadline) {
		if (await tid('foundation-summary-step').isVisible().catch(() => false)) return `${reloads} reloads`;
		const banner = await page.getByText('Something went wrong').first().isVisible().catch(() => false);
		if (banner) log('  page shows "Something went wrong"; reloading');
		await page.waitForTimeout(banner ? 2000 : 60_000);
		if (await tid('foundation-summary-step').isVisible().catch(() => false)) return `${reloads} reloads`;
		await page.reload({ waitUntil: 'domcontentloaded' });
		reloads += 1;
		await tid('course-foundation-wizard').waitFor({ timeout: 60_000 });
		// After a reload the wizard opens on the step that matches the foundation's state.
		const summaryTab = tid('foundation-step-tab-summary');
		if (await summaryTab.isEnabled().catch(() => false)) await summaryTab.click().catch(() => {});
	}
	throw new Error('extraction did not reach the Generation Summary in 25 minutes');
});

await step('summary', async () => {
	await tid('foundation-summary-continue').click();
	await tid('foundation-review-step').waitFor({ timeout: 60_000 });
	await tid('foundation-candidate-list').waitFor({ timeout: 60_000 });
	// Log what a reviewer must decide: assessment weights (they must total 100%) and open conflicts.
	const cards = await page.evaluate(() =>
		[...document.querySelectorAll('[data-testid^="foundation-candidate-card-"]')].map((c) => {
			const lines = c.innerText.split('\n').map((x) => x.trim()).filter(Boolean);
			return { kind: lines[0], title: lines.find((x) => x.length > 3 && !/^(learning outcome|assessment|delivery|aims|official|ai|course identity|\d+ conflicts?)$/i.test(x) && !/^(learning outcome|assessment|delivery|aims and outcomes|official)\b/i.test(x)) ?? '', pct: (c.innerText.match(/\b(\d{1,3})\s?%/) ?? [])[1] };
		}),
	);
	for (const c of cards.filter((x) => /assessment/i.test(x.kind))) log(`  REVIEW assessment: "${c.title.slice(0, 100)}"${c.pct ? ` ${c.pct}%` : ''}`);
	const conflicts = await page.locator('[data-testid^="foundation-conflict-resolve-"]').count();
	log(`  REVIEW open conflicts: ${conflicts}`);
	return `${cards.length} candidates on screen, ${conflicts} conflicts`;
});

async function acceptAllPending() {
	// Accept every section's candidates, then any single pending card. Buttons the app disables (for example
	// while a blocking issue is open) are left alone; validation decides what happens next.
	let accepted = 0;
	const acceptAll = page.locator('[data-testid^="foundation-accept-all-"]');
	for (let i = 0; i < (await acceptAll.count()); i += 1) {
		const b = acceptAll.nth(i);
		if (!(await b.isEnabled({ timeout: 2000 }).catch(() => false))) continue;
		await b.scrollIntoViewIfNeeded();
		await b.click();
		await tid('foundation-accept-all-confirm').click({ timeout: 10_000 });
		await tid('foundation-accept-all-modal').waitFor({ state: 'hidden', timeout: 60_000 });
		accepted += 1;
	}
	const pending = page.locator('[data-testid^="foundation-accept-"]:not([data-testid^="foundation-accept-all"]):not([disabled])');
	for (let i = 0; i < 100 && (await pending.count()) > 0; i += 1) {
		await pending.first().scrollIntoViewIfNeeded();
		await pending.first().click();
		await page.waitForTimeout(500);
		accepted += 1;
	}
	return accepted;
}

async function pendingCount() {
	return page.locator('[data-testid^="foundation-accept-"]:not([data-testid^="foundation-accept-all"])').count();
}

async function waitForValidation() {
	// Validation runs on entering the step. It is finished when Continue is enabled or issues are listed.
	const cont = tid('foundation-validate-continue');
	const deadline = Date.now() + 5 * 60_000;
	while (Date.now() < deadline) {
		if (await cont.isEnabled({ timeout: 2000 }).catch(() => false)) return 'ready';
		if ((await page.locator('[data-testid^="foundation-validation-issue-"][data-testid$="-waive"]').count()) > 0) return 'issues';
		await page.waitForTimeout(3000);
	}
	return 'timeout';
}

async function rejectMatching() {
	if (!REJECT) return 0;
	await page.getByRole('tab', { name: /^all sections/i }).first().click().catch(() => {});
	await page.waitForTimeout(1500);
	for (let i = 0; i < 10; i += 1) {
		const more = page.getByRole('button', { name: /load more/i }).first();
		if (!(await more.isVisible({ timeout: 1000 }).catch(() => false))) break;
		await more.click();
		await page.waitForTimeout(1000);
	}
	let n = 0;
	for (let pass = 0; pass < 50; pass += 1) {
		const cards = page.locator('[data-testid^="foundation-candidate-card-"]');
		let hit = null;
		for (let i = 0; i < (await cards.count()); i += 1) {
			const card = cards.nth(i);
			const id = (await card.getAttribute('data-testid')).replace('foundation-candidate-card-', '');
			const rej = tid(`foundation-reject-${id}`);
			if (!(await rej.isEnabled({ timeout: 500 }).catch(() => false))) continue;
			const lines = (await card.innerText()).split('\n').map((x) => x.trim()).filter(Boolean);
			const line = lines.find((x) => REJECT.test(x));
			if (line) { hit = { id, line }; break; }
		}
		if (!hit) break;
		log(`  operator reject (--reject): "${hit.line.slice(0, 120)}"`);
		await tid(`foundation-reject-${hit.id}`).scrollIntoViewIfNeeded();
		await tid(`foundation-reject-${hit.id}`).click();
		await tid('foundation-reject-reason').fill('Duplicate or roll-up of another assessment component (operator decision via lane flow --reject).').catch(() => {});
		await tid('foundation-reject-confirm').click();
		await tid('foundation-reject-modal').waitFor({ state: 'hidden', timeout: 30_000 });
		await page.waitForTimeout(1000);
		n += 1;
	}
	return n;
}

// --resolve-conflicts: the operator's decision to mark every open conflict "resolved by source
// precedence" (the app keeps the candidates in the queue; accept or reject them separately). Run it
// after --reject has removed the duplicates the conflicts point at.
async function resolveConflicts() {
	if (!args['resolve-conflicts']) return 0;
	let n = 0;
	for (let i = 0; i < 40; i += 1) {
		const btn = page.locator('[data-testid^="foundation-conflict-resolve-"]').first();
		if (!(await btn.isVisible({ timeout: 2000 }).catch(() => false))) break;
		await btn.scrollIntoViewIfNeeded();
		await btn.click();
		await tid('foundation-resolve-conflict-modal').waitFor();
		const desc = (await tid('foundation-resolve-conflict-description').innerText().catch(() => '')).replace(/\s+/g, ' ');
		await tid('foundation-resolve-conflict-option-resolved_by_source_precedence').click();
		await tid('foundation-resolve-conflict-comment').fill(args['resolve-conflicts'] === 'true' ? 'Reviewed by the operator during a lane flow run; duplicates were rejected separately.' : args['resolve-conflicts']);
		await tid('foundation-resolve-conflict-submit').click();
		await tid('foundation-resolve-conflict-modal').waitFor({ state: 'hidden', timeout: 30_000 });
		log(`  operator resolved conflict: ${desc.slice(0, 160)}`);
		n += 1;
		await page.waitForTimeout(1000);
	}
	return n;
}

await step('review-accept-all', async () => {
	const reloadReview = async () => {
		await page.reload({ waitUntil: 'domcontentloaded' });
		await tid('course-foundation-wizard').waitFor({ timeout: 60_000 });
		await tid('foundation-step-tab-review').click();
		await tid('foundation-review-step').waitFor({ timeout: 60_000 });
		await page.waitForTimeout(2000);
	};
	let rejected = await rejectMatching();
	const resolved = await resolveConflicts();
	if (args['resolve-conflicts']) log(`  resolved ${resolved} conflict(s)`);
	// Resolving conflicts unlocks cards that only render after a reload; reject and accept again after it.
	let n = 0;
	for (let pass = 0; pass < 3; pass += 1) {
		n += await acceptAllPending();
		await reloadReview();
		rejected += await rejectMatching();
		if ((await page.locator('[data-testid^="foundation-accept-"]:not([data-testid^="foundation-accept-all"]):not([disabled])').count()) === 0) break;
	}
	if (REJECT) log(`  rejected ${rejected} candidate(s) matching ${REJECT}`);
	await tid('foundation-review-continue').click();
	await tid('foundation-validate-step').waitFor({ timeout: 60_000 });
	return `${n} accept actions, ${await pendingCount()} candidates still pending`;
});

await step('validate-foundation', async () => {
	// Blocking issues are real product results on this PDF, not flow errors. The flow records each one
	// as a FINDING in steps.log, waives it once with a reason (the app's own path for issues raised
	// against accepted content) and revalidates. If validation still blocks, the flow stops here: picking
	// which candidates are duplicates needs a person, so it never accepts or rejects more on its own.
	const notes = [];
	if (!(await tid('foundation-validate-step').isVisible().catch(() => false))) {
		await tid('foundation-step-tab-validate').click();
		await tid('foundation-validate-step').waitFor();
	}
	for (let round = 1; round <= 2; round += 1) {
		const state = await waitForValidation();
		if (state === 'ready') break;
		if (state === 'timeout') throw new Error('validation neither passed nor listed issues in 5 minutes');
		if (round === 2) break;
		const waives = page.locator('[data-testid^="foundation-validation-issue-"][data-testid$="-waive"]');
		const count = await waives.count();
		for (let i = 0; i < count; i += 1) {
			const btn = waives.first();
			const id = (await btn.getAttribute('data-testid')).replace(/^foundation-validation-issue-/, '').replace(/-waive$/, '');
			const text = (await tid(`foundation-validation-issue-${id}`).innerText()).replace(/\s+/g, ' ').slice(0, 700);
			log(`  FINDING blocking validation issue: ${text}`);
			await btn.scrollIntoViewIfNeeded();
			await btn.click();
			await tid(`foundation-validation-issue-${id}-waive-reason`).fill('Waived by the lane golden-path flow; the issue text is recorded as a finding in the proof log.');
			await tid(`foundation-validation-issue-${id}-waive-confirm`).click();
			await page.waitForTimeout(2000);
		}
		notes.push(`waived ${count} blocking issue(s)`);
		await shot('validate-waived');
		const reval = page.locator('[data-testid="foundation-validate-revalidate"], [data-testid="foundation-validation-revalidate"]').first();
		if (await reval.isEnabled({ timeout: 5000 }).catch(() => false)) { await reval.click(); notes.push('revalidated'); }
		await page.waitForTimeout(5000);
	}
	const cont = tid('foundation-validate-continue');
	if (!(await cont.isEnabled({ timeout: 5000 }).catch(() => false))) {
		throw new Error(`validation still blocks approval (${notes.join(', ') || 'no waivable issue'}); see the FINDING lines above. A person must fix the candidates in Review.`);
	}
	await cont.click();
	await tid('foundation-approve-step').waitFor({ timeout: 60_000 });
	return notes.join(', ') || 'passed first time';
});

await step('approve-foundation', async () => {
	await tid('foundation-approve-step').waitFor();
	for (const notice of ['foundation-approval-permission-notice', 'foundation-approval-blocked-notice', 'foundation-approval-not-ready-notice']) {
		if (await tid(notice).isVisible({ timeout: 1000 }).catch(() => false)) throw new Error(`approval not possible: ${(await tid(notice).innerText()).replace(/\s+/g, ' ')}`);
	}
	// The approver confirms the baseline (and, when shown, the wording changes) before the button enables.
	for (const box of ['foundation-approval-confirm-checkbox', 'foundation-approval-wording-checkbox']) {
		const cb = tid(box);
		if (await cb.isVisible({ timeout: 2000 }).catch(() => false)) {
			await cb.scrollIntoViewIfNeeded();
			if (!(await cb.isChecked())) await cb.check();
		}
	}
	const confirm = tid('foundation-confirm-approval');
	if (await confirm.isVisible({ timeout: 3000 }).catch(() => false)) {
		await confirm.scrollIntoViewIfNeeded();
		await confirm.click();
	}
	const cont = tid('foundation-approve-continue');
	const deadline = Date.now() + 60_000;
	while (Date.now() < deadline && !(await cont.isEnabled().catch(() => false))) await page.waitForTimeout(2000);
	if (!(await cont.isEnabled())) throw new Error('approve did not enable Create Smart Syllabus');
});

await step('create-smart-syllabus', async () => {
	// After approval the wizard shows how the foundation maps into a syllabus and a "Launch Smart Syllabus"
	// button (older builds used foundation-approve-continue).
	const created = page.waitForResponse(
		(r) => r.request().method() === 'POST' && /smart-syllabus/.test(r.url()) && /course-foundation/.test(r.url()),
		{ timeout: 180_000 },
	).catch(() => null);
	// Two clicks: "Create Smart Syllabus" on Approve opens a mapping preview, and "Launch Smart Syllabus"
	// there (enabled once the preview loads) creates it.
	const confirm = tid('foundation-confirm-create-syllabus');
	if (!(await confirm.isVisible({ timeout: 3000 }).catch(() => false))) {
		if (!(await tid('foundation-approve-continue').isVisible({ timeout: 3000 }).catch(() => false))) await tid('foundation-step-tab-approve').click();
		await tid('foundation-approve-continue').click();
	}
	await confirm.waitFor();
	const until = Date.now() + 60_000;
	while (Date.now() < until && !(await confirm.isEnabled().catch(() => false))) await page.waitForTimeout(1000);
	await confirm.click();
	const res = await created;
	if (res && !res.ok()) throw new Error(`create syllabus -> ${res.status()} ${(await res.text()).slice(0, 200)}`);
	if (res) {
		const body = await res.json().catch(() => ({}));
		state.syllabusId = body.smartSyllabusVersionId ?? body.id;
	}
	await page.waitForURL(/\/syllabus\/[^/]+\//, { timeout: 180_000 });
	state.syllabusId ??= new URL(page.url()).pathname.split('/')[2];
	await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => {});
	const v = await api(`/smart-syllabus/versions/${state.syllabusId}`);
	return `syllabus ${state.syllabusId}: ${v.learningOutcomes?.length ?? '?'} outcomes, ${v.syllabusModules?.length ?? '?'} modules`;
});

await step('publish-validate', async () => {
	await goto(`/syllabus/${state.syllabusId}/publish`);
	await page.getByRole('button', { name: 'Validate' }).click();
	const publish = tid('publish-syllabus-button');
	await publish.waitFor({ timeout: 120_000 });
	await page.waitForTimeout(3000);
	const body = (await page.locator('main').innerText()).replace(/\s+/g, ' ');
	const verdict = /Validation Passed/i.test(body) ? 'passed' : /Validation Failed/i.test(body) ? 'failed' : 'unknown';
	if (!(await publish.isEnabled())) {
		throw new Error(`publish blocked, validation ${verdict}: ${body.slice(body.search(/Validation/i), body.search(/Validation/i) + 600)}`);
	}
	return `validation ${verdict}`;
});

await step('publish', async () => {
	await tid('publish-syllabus-button').click();
	await page.getByRole('button', { name: 'Confirm & Go Live' }).click();
	await page.getByText(/Syllabus is Published/i).first().waitFor({ timeout: 120_000 });
	const v = await api(`/smart-syllabus/versions/${state.syllabusId}`);
	return `status ${v.status ?? '?'}`;
});

log(`DONE course=${state.courseId} syllabus=${state.syllabusId}`);
await close();
