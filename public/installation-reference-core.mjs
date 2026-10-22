// A guide is stored once. Materials/tasks contain identifiers, never copies.
export const GUIDE_STATES = ['Draft', 'Reviewed', 'Archived'];
export function httpsUrl(value) {
  if (!value) return '';
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password) throw Error('Use an HTTPS source URL without credentials.');
  return url.href;
}
const ids = values => [...new Set((values || []).filter(v => typeof v === 'string' && v.trim()).map(v => v.trim()))];
export function validateGuide(input) {
  const title = String(input.title || '').trim();
  if (!title || title.length > 160) throw Error('Enter a title of up to 160 characters.');
  const status = input.status || 'Draft';
  if (!GUIDE_STATES.includes(status)) throw Error('Invalid review status.');
  const sources = (input.sources || []).map(source => ({
    kind: ['Manufacturer', 'Massachusetts code', 'Field example', 'Other'].includes(source.kind) ? source.kind : 'Other',
    title: String(source.title || '').trim(),
    url: httpsUrl(source.url),
    section: String(source.section || '').trim(),
    edition: String(source.edition || '').trim(),
    checkedAt: String(source.checkedAt || '').trim()
  }));
  if (status === 'Reviewed' && (!input.reviewedBy || !input.reviewedAt || !sources.length || !sources.every(s => s.title && s.checkedAt && (s.url || s.kind === 'Field example')))) {
    throw Error('A reviewed guide needs a reviewer, review date and identified, dated sources.');
  }
  return {
    title, category: String(input.category || 'Other').trim(),
    description: String(input.description || '').trim(), status,
    materialIds: ids(input.materialIds), taskTypeIds: ids(input.taskTypeIds),
    photos: (input.photos || []).map(p => ({url: httpsUrl(p.url), caption: String(p.caption || '').trim()})),
    sources, reviewedBy: status === 'Reviewed' ? input.reviewedBy : null,
    reviewedAt: status === 'Reviewed' ? input.reviewedAt : null
  };
}
// No title-based guessing: 'install lights' does not identify a luminaire.
export function referencesForTask(task, guides) {
  const explicit = new Set(ids(task.referenceIds));
  const materialIds = new Set(ids([task.materialId, task.matId, ...(task.materialIds || [])]));
  return guides.filter(g => g.status !== 'Archived' && (
    explicit.has(g.id) ||
    (g.status === 'Reviewed' && ((g.materialIds || []).some(id => materialIds.has(id)) ||
      (!!task.taskTypeId && (g.taskTypeIds || []).includes(task.taskTypeId))))
  ));
}
export function updateGuide(previous, input, actor, now = new Date().toISOString()) {
  if (!actor) throw Error('Sign in before saving a reference.');
  if ((previous?.revision || 0) !== (input.revision || 0)) throw Error('This guide changed. Reopen the latest version.');
  const clean = validateGuide(input);
  // Changing instructional content always requires a fresh review.
  if (previous?.status === 'Reviewed') {
    const before = validateGuide(previous);
    const changed = ['title', 'description', 'photos', 'sources', 'materialIds', 'taskTypeIds'].some(key => JSON.stringify(before[key]) !== JSON.stringify(clean[key]));
    if (changed) { clean.status = 'Draft'; clean.reviewedBy = null; clean.reviewedAt = null; }
  }
  return {...clean, createdBy: previous?.createdBy || actor, createdAt: previous?.createdAt || now,
    updatedBy: actor, updatedAt: now, revision: (previous?.revision || 0) + 1};
}
