// Shared catalog taxonomy. Reading old records never rewrites stored material data.
export const FAMILIES=[
 ['grounding','Grounding & bonding',/ground.?rod|grounding|bonding|aterramento/i,'⏚'],
 ['datacom','Data & networking',/cat.?[56]|ethernet|rj.?45|keystone|patch.?panel|network|coax/i,'⌁'],
 ['solar','Solar products',/solar|photovoltaic|inverter|mc.?4|pv.?wire/i,'☀'],
 ['ev','EV chargers',/evse|ev.?charger|carregador/i,'⚡'],
 ['breakers','Circuit breakers',/breaker|disjuntor/i,'▥'],
 ['disconnects','Disconnects',/disconnect|safety.?switch/i,'▥'],
 ['panels','Panels & load centers',/panel|painel|load.?center|meter|ground.?bar/i,'▥'],
 ['fittings','Connectors & fittings',/connector|conector|coupling|bushing|bucha|locknut|elbow|condulet|conduit body|adapter|adaptador/i,'⊙'],
 ['conduit','Conduit & raceways',/conduit|eletroduto|\bemt\b|\brmc\b|\bimc\b|wiremold|raceway|liquid.?tight|smurf/i,'∿'],
 ['cable','Wire & cable',/wire|cable|cabo|condutor|conductor/i,'〰'],
 ['boxes','Boxes & covers',/box|caixa|cover|tampa|mud.?ring|plaster.?ring|gang.?ring/i,'□'],
 ['lighting','Lighting',/light|led|lamp|lumin|recess|downlight|ballast|driver|trim/i,'☀'],
 ['devices','Outlets & switches',/receptacle|outlet|tomada|switch|interruptor|gfci|afci|dimmer|wall.?plate/i,'▣'],
 ['detection','Smoke & heat detection',/smoke|heat.?detect|detector|carbon.?monoxide|\bsmco\b/i,'◉'],
 ['notification','Horns, strobes & speakers',/horn|strobe|speaker|notification|sounder/i,'◖'],
 ['fire-controls','Fire alarm controls',/fire.?alarm|alarm.?panel|module|modulo|pull.?station|annunciator|monitor|booster/i,'⊞'],
 ['supports','Supports & hardware',/clamp|strap|abracadeira|hanger|bracket|strut|screw|bolt|anchor|nut|support|staple/i,'⊡'],
 ['tools','Tools & accessories',/tool|drill|bit\b|blade|tape|label|marker|sealant|caulk/i,'⌕'],
 ['other','Other products',null,'…']
];
const legacy={wiring:'cable',accessories:'supports',detectors:'detection',notification:'notification'};
export function familyOf(m){
 if(FAMILIES.some(f=>f[0]===m.catalogFamily))return m.catalogFamily;
 const old=m.family||m.subcategory;
 // The original "breakers" family included panels and disconnects.
 if(old==='breakers'){if(/disconnect|safety.?switch/i.test(m.name))return 'disconnects';if(!/breaker|disjuntor/i.test(m.name)&&/panel|painel|load.?center|meter|ground.?bar/i.test(m.name))return 'panels';return 'breakers';}
 if(legacy[old])return legacy[old];if(FAMILIES.some(f=>f[0]===old))return old;
 if(m.cat==='fire'&&/panel|module|pull.?station|annunciator|monitor|booster/i.test(m.name))return 'fire-controls';
 return FAMILIES.find(f=>f[2]?.test(m.name||''))?.[0]||'other';
}
export const PROTECTIONS=['Standard','AFCI','GFCI','Dual Function'];
export const PRODUCT_TYPES={
 conduit:['EMT','PVC','Rigid / IMC','Flexible metal','Liquidtight','ENT','Raceway'],
 fittings:['Connector','Coupling','Bushing','Locknut','Elbow','Conduit body','Adapter'],
 boxes:['Box','Cover','Mud ring'],devices:['Receptacle','Switch','Dimmer','Wall plate'],
 cable:['Building wire','NM cable','MC cable','Low-voltage cable'],panels:['Load center','Panelboard','Meter socket','Panel accessory'],
 disconnects:['Fused','Non-fused'],lighting:['Fixture','Lamp','Driver','Trim'],
 supports:['Strap','Clamp','Hanger','Strut','Fastener'],grounding:['Ground rod','Ground wire','Bonding accessory'],
 detection:['Smoke detector','Heat detector','CO detector','Combination detector'],notification:['Horn','Strobe','Horn / strobe','Speaker'],
 'fire-controls':['Control panel','Module','Pull station','Annunciator'],datacom:['Data cable','Jack','Patch panel','Accessory'],solar:['Inverter','PV wire','Connector','Accessory'],ev:['EV charger','Accessory']
};
const dedupe=a=>[...new Set(a.filter(v=>v!==undefined&&v!==null&&String(v).trim()).map(String))];
export function canonicalSize(value){
 let s=String(value||'').toLowerCase().replace(/[¼½¾⅛⅜⅝⅞]/g,c=>' '+({'¼':'1/4','½':'1/2','¾':'3/4','⅛':'1/8','⅜':'3/8','⅝':'5/8','⅞':'7/8'}[c])).replace(/\bhalf\s*(?:an?\s*)?(?:inch|inches)\b/g,'1/2 in').replace(/\bthree[ -]quarters?\s*(?:inch|inches)\b/g,'3/4 in').replace(/\bquarter\s*(?:inch|inches)\b/g,'1/4 in').replace(/\s*\/\s*/g,'/').trim();
 const hit=s.match(/^(\d+)(?:[ -]+(\d+)\/(\d+))?\s*(?:in\.?|inch(?:es)?|["″])?$|^(\d+)\/(\d+)\s*(?:in\.?|inch(?:es)?|["″])?$|^(\d*\.\d+)\s*(?:in\.?|inch(?:es)?|["″])?$/i);
 if(!hit)return s.replace(/inches|inch|["″]/g,'in.').replace(/\s+/g,' ');
 let n=hit[6]?Number(hit[6]):hit[4]?Number(hit[4])/Number(hit[5]):Number(hit[1])+(hit[2]?Number(hit[2])/Number(hit[3]):0);
 if(!Number.isFinite(n)||n<=0)return s;
 const whole=Math.floor(n),eighth=Math.round((n-whole)*8);if(Math.abs(n-(whole+eighth/8))>0.00001)return n+' in.';
 const fractions=['','1/8','1/4','3/8','1/2','5/8','3/4','7/8'];return (eighth===8?String(whole+1):eighth?(whole?whole+'-':'')+fractions[eighth]:String(whole))+' in.';
}
export function tradeSizes(m){
 const explicit=m.tradeSize||(m.size&&['conduit','fittings','supports'].includes(familyOf(m))?m.size:'');if(explicit)return [canonicalSize(explicit)];
 if(!['conduit','fittings','supports'].includes(familyOf(m)))return [];
 const text=String(m.name||'').replace(/[¼½¾⅛⅜⅝⅞]/g,c=>' '+({'¼':'1/4','½':'1/2','¾':'3/4','⅛':'1/8','⅜':'3/8','⅝':'5/8','⅞':'7/8'}[c])).replace(/\bhalf\s*inch\b/gi,'1/2 in.');
 return dedupe([...text.matchAll(/\b(\d+[ -]+\d+\/\d+|\d+\/\d+|\d*\.\d+|\d+)\s*(?:in(?:ch(?:es)?)?\.?\b|["″])/gi)].map(h=>canonicalSize(h[1])));
}
export function ampRatings(m){if(m.amperage)return [String(m.amperage).replace(/\s*(?:amps?|amperes?|A)$/i,'').trim()+' A'];return dedupe([...String(m.name||'').matchAll(/\b(\d+(?:\.\d+)?)\s*(?:amp(?:s|ere)?|A)\b/gi)].map(h=>h[1]+' A'));}
export function protectionOf(m){
 if(PROTECTIONS.includes(m.protection))return m.protection;
 const text=m.name||'';if(/dual[ -]?function|\b(?:afci\s*[/+&-]\s*gfci|gfci\s*[/+&-]\s*afci)\b/i.test(text))return 'Dual Function';
 if(/\bafci\b|arc[ -]?fault/i.test(text)&&/\bgfci\b|ground[ -]?fault/i.test(text))return 'Dual Function';
 if(/\bafci\b|arc[ -]?fault/i.test(text))return 'AFCI';if(/\bgfci\b|ground[ -]?fault/i.test(text))return 'GFCI';
 return /\bstandard\b/i.test(text)?'Standard':''; // Missing protection must never mean Standard.
}
export function typeOf(m){
 if(familyOf(m)==='breakers')return protectionOf(m);if(m.productType)return m.productType;
 const types=PRODUCT_TYPES[familyOf(m)]||[];return types.find(t=>new RegExp('\\b'+t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','i').test(m.name||''))||'';
}
export const FACETS=[['Brand','brand'],['Subcategory','type'],['Trade size','size'],['Amperage','amps'],['Series','series'],['Poles','poles'],['Voltage','voltage'],['Neutral connection','neutral'],['Wire gauge (AWG)','wireGauge'],['Cable configuration','cableConfiguration'],['Dimensions','dimensions'],['Length','length'],['Color / finish','finish'],['Supplier in library','supplier']];
const electrical=['breakers','panels','disconnects','devices','ev'];
export function facetKeys(family){return ['brand',...(family==='all'?[]:['type',...(['conduit','fittings','supports'].includes(family)?['size']:[]),...(electrical.includes(family)?['amps','series','voltage']:[]),...(family==='breakers'?['poles','neutral']:[]),...(family==='cable'?['wireGauge','cableConfiguration','length']:[]),...(['boxes','lighting','supports'].includes(family)?['dimensions']:[]),...(['conduit','supports'].includes(family)?['length']:[]),...(['devices','lighting','boxes'].includes(family)?['finish']:[])]),'supplier'];}
export function attributeValues(m,key){
 if(key==='type')return typeOf(m)?[typeOf(m)]:[];if(key==='size')return tradeSizes(m);if(key==='amps')return ampRatings(m);
 if(key==='poles'){if(m.poles)return [String(m.poles)];const hit=String(m.name||'').match(/\b([1234])\s*[- ]?poles?\b/i);return hit?[hit[1]]:[];}
 if(key==='voltage'){if(m.voltage)return [String(m.voltage).replace(/\s*V$/i,'')+' V'];const hit=String(m.name||'').match(/\b(\d+(?:\/\d+)?)\s*(?:volts?|V)\b/i);return hit?[hit[1]+' V']:[];}
 if(key==='neutral')return m.neutralConnection?[m.neutralConnection]:[];
 return m[key]?[String(m[key])]:[];
}
export function compatibilityVerified(m){try{return m.compatibilityStatus==='verified'&&!!m.compatiblePanels?.trim()&&new URL(m.compatibilitySource).protocol==='https:';}catch{return false;}}
export function variantKey(m){return m.variantGroup?.trim()&&m.brand?.trim()?[familyOf(m),m.brand.trim().toLowerCase(),m.variantGroup.trim().toLowerCase()].join('|'):'';}
export function groupVariants(rows){const groups=new Map();for(const m of rows){const key=variantKey(m);if(key){if(!groups.has(key))groups.set(key,[]);groups.get(key).push(m);}}const seen=new Set();return rows.flatMap(m=>{const key=variantKey(m),variants=groups.get(key);if(!key||variants.length<2)return [{material:m,variants:[m]}];if(seen.has(key))return [];seen.add(key);return [{material:m,variants}];});}
export function validateAttributes(p){
 if(p.amperage!==''&&p.amperage!=null&&(!/^\d+(?:\.\d+)?$/.test(String(p.amperage))||Number(p.amperage)<=0))throw Error('Enter a positive amperage in A.');
 if(p.poles&&!['1','2','3','4'].includes(String(p.poles)))throw Error('Select a pole count from 1 to 4.');
 if(p.variantGroup?.trim()&&!p.brand?.trim())throw Error('Enter a manufacturer before grouping variants.');
 if(p.compatibilityStatus==='verified'&&!compatibilityVerified(p))throw Error('Verified compatibility requires panel models and an HTTPS manufacturer reference.');
}
