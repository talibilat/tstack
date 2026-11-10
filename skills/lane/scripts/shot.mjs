// Usage (via `lane shot <N> <path> <out.png> [--as EMAIL]`): log in through the real UI, open <path>,
// wait for the page to settle and save a full-page screenshot. Prints the final URL and page title.
import { openLane } from './browser.mjs';

const [path, out, as] = process.argv.slice(2);
if (!path || !out) {
	console.error('usage: shot.mjs <path> <out.png> [email]');
	process.exit(2);
}
const { page, goto, close } = await openLane({ as });
try {
	await goto(path);
	await page.screenshot({ path: out, fullPage: true });
	console.log(`${page.url()}  "${await page.title()}"  -> ${out}`);
} finally {
	await close();
}
