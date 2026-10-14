const idPattern = /^[a-zA-Z0-9_-]{1,80}$/;
export function companyScope(companyId) {
  if (!idPattern.test(companyId || '')) throw new Error('Invalid company identity');
  const base = 'companies/' + companyId;
  const safe = value => {
    if (typeof value !== 'string' || !value || value.split('/').some(p => !p || p === '.' || p === '..')) throw new Error('Invalid company path');
    if (/^(https?:|gs:|companies\/)/i.test(value)) throw new Error('Use a company-relative path');
    return value;
  };
  return Object.freeze({companyId,
    collection: name => {
      if (!idPattern.test(name) || name === 'members') throw new Error('Invalid data collection');
      return base + '/' + name;
    },
    document: (name, id) => {
      if (!idPattern.test(name) || name === 'members' || !idPattern.test(id)) throw new Error('Invalid data document');
      return base + '/' + name + '/' + id;
    },
    file: path => base + '/' + safe(path),
    record: value => {
      if (value.companyId && value.companyId !== companyId) throw new Error('Company mismatch');
      return {...value, companyId};
    },
    queueKey: uid => {
      if (!idPattern.test(uid)) throw new Error('Invalid user identity');
      return 'obraUploadQueue:' + companyId + ':' + uid;
    }
  });
}
export function companyBrand(company) {
  return {
    name: String(company?.name || '').trim(),
    phone: String(company?.phone || '').trim(),
    email: String(company?.email || '').trim(),
    website: String(company?.website || '').trim(),
    license: String(company?.license || '').trim(),
    logoPath: String(company?.logoPath || '').trim()
  };
}
