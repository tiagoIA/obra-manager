export {normalizeSearch,matchesMaterial} from './product-search.js?v=material-variants-20261016';
export function selectedSummary(items){return {count:items.length,incomplete:items.filter(i=>!i.name?.trim()||!i.unit?.trim()||!Number.isFinite(Number(i.qty))||Number(i.qty)<=0).length};}
