const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync('public/app.html', 'utf8');
for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  if (!match[2].trim()) continue;
  if (/type=["']module["']/.test(match[1])) new vm.SourceTextModule(match[2]);
  else new vm.Script(match[2]);
}
for (const path of ['photo-report.js', 'unit-report-structure.js']) {
  new vm.SourceTextModule(fs.readFileSync('public/' + path, 'utf8'));
}
let printed = '';
const elements = {
  'pdf-content': {dataset: {reportProjectName: '1511 Main St., Worcester'}, lang: 'en', outerHTML: '<article>Report</article>', querySelector: () => null},
  'shop-pdf-content': {dataset: {reportProjectName: 'Roof & HVAC'}, lang: 'en', outerHTML: '<article>Shopping</article>', querySelector: () => null}
};
const context = vm.createContext({
  window: {open: () => ({document: {write: value => {printed = value;}, close: () => {}}})},
  document: {getElementById: id => elements[id], styleSheets: [], querySelectorAll: () => []},
  x: value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;'),
  activePid: 'different-project', projects: {'different-project': {name: 'Wrong project'}}
});
const start = html.indexOf('window.reportPDFTitle=function');
const end = html.indexOf('window.shareWhatsApp=function', start);
assert.ok(start > 0 && end > start);
vm.runInContext(html.slice(start, end), context);
context.window.printPDF();
assert.match(printed, /<title>1511 Main St\., Worcester<\/title>/);
assert.ok(!printed.includes('Wrong project'));
context.window.printPDF('shop');
assert.match(printed, /<title>Roof &amp; HVAC<\/title>/);
elements['pdf-content'].dataset.reportProjectName = 'A </title><script>alert(1)</script>';
context.window.printPDF();
assert.match(printed, /<title>A &lt;\/title&gt;&lt;script&gt;alert\(1\)&lt;\/script&gt;<\/title>/);
let delegated = false;
elements['pdf-content'].querySelector = () => ({});
context.window.photoReport = {print: element => {delegated = element === elements['pdf-content'];}};
context.window.printPDF();
assert.equal(delegated, true);
console.log('Report titles: syntax, project binding, shopping, escaping and photo delegation passed.');
