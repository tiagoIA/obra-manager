import {canonicalSize} from './material-attributes.js?v=1';
// Shared matching for shopping lists. Never changes product specifications.
export function normalizeSearch(value){
 return String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
 .replace(/\bhalf\s*(?:an?\s*)?inch(?:es)?\b/gi,'1/2 in').replace(/\bthree[ -]quarters?\s*inch(?:es)?\b/gi,'3/4 in').replace(/\bquarter\s*inch(?:es)?\b/gi,'1/4 in')
 .replace(/[¼½¾⅛⅜⅝⅞]/g,c=>({'¼':' 1/4','½':' 1/2','¾':' 3/4','⅛':' 1/8','⅜':' 3/8','⅝':' 5/8','⅞':' 7/8'}[c]))
 .replace(/(\d+(?:\.\d+)?|\d*\.\d+)\s*(?:(?:inches|inch|in)\b\.?|["″])/gi,v=>canonicalSize(v))
 .replace(/(\d)\s*\/\s*(\d)/g,'$1/$2').replace(/[^a-z0-9/]+/g,' ').trim();
}
const aliases={cabo:'cable',cabos:'cable',fio:'wire',fios:'wire',disjuntor:'breaker',disjuntores:'breaker',tomada:'receptacle',tomadas:'receptacle',conector:'connector',conectores:'connector',interruptor:'switch',interruptores:'switch',eletroduto:'conduit',painel:'panel',carregador:'charger',placa:'plate',bucha:'bushing',abracadeira:'clamp'};
const synonyms={cable:['cable','cabo','cabos'],wire:['wire','fio','fios'],breaker:['breaker','disjuntor','disjuntores'],receptacle:['receptacle','outlet','tomada','tomadas'],connector:['connector','conector','conectores'],switch:['switch','interruptor','interruptores'],conduit:['conduit','eletroduto'],panel:['panel','painel'],charger:['charger','carregador'],plate:['plate','placa'],bushing:['bushing','bucha'],clamp:['clamp','abracadeira']};
export function matchesMaterial(material,query){
 const text=normalizeSearch([material.name,material.sku,material.brand,material.manufacturerPart,material.model,material.upc,material.family,material.subcategory,material.productType,material.protection,material.tradeSize?canonicalSize(material.tradeSize):'',material.amperage,material.series,material.poles,material.voltage,material.neutralConnection,material.wireGauge,material.cableConfiguration,material.dimensions,material.length,material.finish,material.variantGroup,...(material.aliases||[]),...(material.suppliers||[]).flatMap(s=>[s.name,s.code,s.internetId,...(s.aliasCodes||[])])].filter(Boolean).join(' '));
 return normalizeSearch(query).split(/\s+/).filter(t=>t&&!['in','inch','inches'].includes(t)).every(token=>{const canonical=aliases[token]||token;const terms=synonyms[canonical]||[token];return terms.some(t=>text.includes(t));});
}
export function selectedSummary(items){return {count:items.length,incomplete:items.filter(i=>!i.name?.trim()||!i.unit?.trim()||!Number.isFinite(Number(i.qty))||Number(i.qty)<=0).length};}
