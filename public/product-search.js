import {canonicalSize,familyOf} from './material-attributes.js?v=1';
// Search vocabulary only. Never changes product identity or compatibility.
export const VOCABULARY=[
 ['breaker','breakers','disjuntor','disjuntores'],['wire','wires','cable','cables','fio','fios','cabo','cabos'],
 ['connector','connectors','conector','conectores'],['conduit','conduits','eletroduto','eletrodutos'],
 ['receptacle','receptacles','outlet','outlets','tomada','tomadas'],['switch','switches','interruptor','interruptores'],
 ['panel','panels','painel','paineis'],['bushing','bushings','bucha','buchas'],['clamp','clamps','abracadeira','abracadeiras'],
 ['coupling','couplings','luva','luvas'],['box','boxes','caixa','caixas'],['charger','chargers','carregador','carregadores'],
 ['grounding','aterramento'],['screw','screws','parafuso','parafusos'],['light','lights','luminaria','luminarias'],
 ['gfci','groundfault'],['afci','arcfault']
];
export function normalizeSearch(value){return String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
 .replace(/\bhalf\s*(?:an?\s*)?inch(?:es)?\b/g,'1/2 in').replace(/\bthree[ -]quarters?\s*inch(?:es)?\b/g,'3/4 in').replace(/\bquarter\s*inch(?:es)?\b/g,'1/4 in')
 .replace(/[¼½¾⅛⅜⅝⅞]/g,c=>' '+({'¼':'1/4','½':'1/2','¾':'3/4','⅛':'1/8','⅜':'3/8','⅝':'5/8','⅞':'7/8'}[c]))
 .replace(/\b(\d{1,2})\s*[-/]\s*([234])\b/g,'$1/$2')
 .replace(/(\d+(?:\.\d+)?|\d*\.\d+)\s*(?:(?:inches|inch|in)\b\.?|["″])/g,v=>canonicalSize(v))
 .replace(/\b(\d+(?:\.\d+)?)\s*(amps?|amperes?|a)\b/g,'$1 a')
 .replace(/\bground[ -]fault\b/g,'groundfault').replace(/\barc[ -]fault\b/g,'arcfault')
 .replace(/(\d)\s*\/\s*(\d)/g,'$1/$2').replace(/[^a-z0-9/]+/g,' ').trim();}
const words=value=>normalizeSearch(value).split(/\s+/).filter(t=>t&&!['in','inch','inches','a','amp','amps','awg'].includes(t));
export function productText(m){return [m.name,m.sku,m.brand,m.manufacturerPart,m.model,m.upc,m.description,m.specs,m.family,m.catalogFamily,m.subcategory,m.productType,m.protection,m.tradeSize?canonicalSize(m.tradeSize):'',m.amperage,m.series,m.poles,m.voltage,m.neutralConnection,m.wireGauge,m.cableConfiguration,m.dimensions,m.length,m.finish,m.variantGroup,...(Array.isArray(m.aliases)?m.aliases:[]),...(m.suppliers||[]).flatMap(s=>[s.name,s.code,s.internetId,...(s.aliasCodes||[])])].filter(Boolean).join(' ');}
const synonym=t=>VOCABULARY.find(group=>group.includes(t))||[t];
function oneEdit(a,b){if(Math.abs(a.length-b.length)>1)return false;let i=0,j=0,n=0;while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;continue;}if(++n>1)return false;if(a.length>=b.length)i++;if(b.length>=a.length)j++;}return n+(i<a.length||j<b.length?1:0)<=1;}
export function searchScore(m,query){const tokens=words(query);if(!tokens.length)return 1;const text=normalizeSearch(productText(m)),set=new Set(words(productText(m)));let score=0;
 for(const token of tokens){const terms=synonym(token);if(terms.some(t=>set.has(t))){score+=20;continue;}
 // Numeric specifications and alphanumeric models must match complete tokens.
 if(/\d/.test(token))return 0;
 if(terms.some(t=>t.length>=3&&[...set].some(w=>!/[0-9]/.test(w)&&w.startsWith(t)))){score+=8;continue;}
 if(token.length>=5&&[...set].some(w=>/^[a-z]+$/.test(w)&&oneEdit(token,w))){score+=3;continue;}return 0;
 }
 const q=normalizeSearch(query);if([m.sku,m.manufacturerPart,m.model,m.upc,...(m.suppliers||[]).flatMap(s=>[s.code,s.internetId,...(s.aliasCodes||[])])].some(v=>v&&normalizeSearch(v)===q))score+=1000;
 if(normalizeSearch(m.name)===q)score+=200;else if(text.includes(q))score+=30;return score;}
export const matchesMaterial=(m,q)=>searchScore(m,q)>0;
export function rankProducts(rows,q){return [...rows].sort((a,b)=>searchScore(b,q)-searchScore(a,q)||a.name.localeCompare(b.name));}
