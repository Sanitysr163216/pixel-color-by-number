// Packs the built game (dist/) into one self-contained HTML file that opens with a double-click.
//
//   node scripts/single-file.mjs [output.html] [--fragment]
//
// --fragment leaves out <!doctype>, <html>, <head> and <body>, for hosts that add their own page wrapper.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const fragment = args.includes('--fragment');
const out = args.find((a) => !a.startsWith('--')) ?? 'dist/shoto.html';

let html = readFileSync('dist/index.html', 'utf8');
html = html.replace(/<script type="module" crossorigin src="\.\/(assets\/[^"]+\.js)"><\/script>/, (_, file) => {
  const js = readFileSync(join('dist', file), 'utf8').replace(/<\/script/gi, '<\\/script');
  return `<script type="module">${js}</script>`;
});
html = html.replace(/<link rel="stylesheet" crossorigin href="\.\/(assets\/[^"]+\.css)">/, (_, file) => {
  return `<style>${readFileSync(join('dist', file), 'utf8')}</style>`;
});
if (/src="\.\/assets\//.test(html)) throw new Error('a file from dist/assets was not inlined');

if (fragment) {
  html = html
    .replace(/<!doctype html>\s*/i, '')
    .replace(/<\/?html[^>]*>\s*/gi, '')
    .replace(/<\/?head>\s*/gi, '')
    .replace(/<\/?body>\s*/gi, '')
    .replace(/<meta charset="utf-8">\s*/i, '')
    .replace(/<meta name="viewport"[^>]*>\s*/i, '');
}
writeFileSync(out, html);
console.log(`wrote ${out} (${Math.round(html.length / 1024)} KB)`);
