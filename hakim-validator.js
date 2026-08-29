/* HAKIM Ω Validator v4 — deterministic quality gate + auto-repair + math/RTL QA */
(function(){'use strict';
const E='٠١٢٣٤٥٦٧٨٩';
function normalize(t){return String(t||'').replace(/\r/g,'').replace(/[ \t]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').trim()}
function fp(s){return normalize(s).replace(/\s+/g,' ').replace(/[٠-٩\d]/g,'#').toLowerCase().slice(0,500)}
function blocks(t){return normalize(t).split(/\n\s*(?=---|#{1,3}\s|\*\*[^*]+\*\*|\d+[.)]\s)/).map(x=>x.trim()).filter(x=>x.length>20)}
function cleanRepetition(t){let b=blocks(t),seen=new Set(),out=[];for(const x of b){const k=fp(x);if(!seen.has(k)){seen.add(k);out.push(x)}}let s=out.join('\n\n---\n\n');const lines=s.split('\n'),freq=new Map();for(const l of lines){const k=fp(l);if(k.length>35)freq.set(k,(freq.get(k)||0)+1)}return lines.filter(l=>{const k=fp(l);return !(k.length>35&&freq.get(k)>3)}).join('\n').replace(/(?:\n\s*---\s*){2,}/g,'\n---\n').trim()}
function repetition(t){const b=blocks(t),seen=new Map,dupes=[];for(const x of b){const k=fp(x);if(seen.has(k))dupes.push(k);else seen.set(k,1)}return dupes}
function validateText(text,opts={}){const e=[],t=normalize(text);if(!t)e.push('EMPTY_OUTPUT');if(t&&!/[\u0600-\u06ff]/.test(t))e.push('ARABIC_TEXT_MISSING');if(t.length<80&&opts.long)e.push('OUTPUT_TOO_SHORT');if(t.length>24000)e.push('OUTPUT_TOO_LONG');if(/TODO|TBD|lorem ipsum/i.test(t))e.push('PLACEHOLDER_CONTENT');if(/\b(api key|secret key|password)\b/i.test(t))e.push('SENSITIVE_CONTENT');if(/يقبل\s+٤/.test(t)&&/يأتي بعد\s+٢/.test(t))e.push('PEDAGOGICAL_SEQUENCE_WORDING_ERROR');const d=repetition(t);if(d.length)e.push('REPETITIVE_BLOCKS:'+d.length);const longRepeat=t.match(/(.{35,180})(?:\n\s*\1){2,}/s);if(longRepeat)e.push('REPEATED_TAIL');if(/\b(?:×|÷)\b/.test(t)&&/العدد\s+[٠-٩]/.test(t)&&!/ضرب|قسمة/.test(t))e.push('UNREQUESTED_ADVANCED_OPERATION');return{ok:e.length===0,errors:e}}
function value(s){const n=String(s).replace(/[٠-٩]/g,c=>E.indexOf(c));return /^\d+$/.test(n)?Number(n):null}
function validateMath(text){const e=[],t=String(text||'');if(/\d\s*[+×*÷\-]\s*\d\s*=\s*[\d□]/.test(t))e.push('LATIN_NUMERALS_IN_MATH');for(const m of t.matchAll(/([٠-٩]+)\s*([+×*÷\-])\s*([٠-٩]+)\s*=\s*([٠-٩]+)/g)){const a=value(m[1]),op=m[2],b=value(m[3]),r=value(m[4]);let ok=true;if(op==='+')ok=a+b===r;if(op==='-')ok=a-b===r;if(op==='×')ok=a*b===r;if(op==='÷')ok=b!==0&&a%b===0&&a/b===r;if(!ok)e.push('MATH_EQUATION_ERROR:'+m[0])}if(/([٠-٩]+)\s*[+×*÷\-]\s*([٠-٩]+)\s*=\s*□/.test(t))e.push('MATH_VISUAL_ORDER_REQUIRES_EXPLICIT_RESULT_ORDER');return{ok:e.length===0,errors:e}}
function clean(text){return cleanRepetition(normalize(text))}
function gate(text,opts){const original=normalize(text),repaired=clean(original),a=validateText(repaired,opts),b=validateMath(repaired);return{ok:a.ok&&b.ok,errors:[...a.errors,...b.errors],text:repaired,repaired:repaired!==original,checkedAt:new Date().toISOString()}}
window.HAKIM_VALIDATOR={validateText,validateMath,clean,validate(text,opts){return gate(text,opts)}};
/* Export and display are both forced through the same quality-gated text. */
if(window.HAKIM_ENGINE&&window.HAKIM_ENGINE.build){const old=window.HAKIM_ENGINE.build;window.HAKIM_ENGINE.build=function(text){const g=gate(text,{long:true});if(!g.ok)throw Error('NO-GO: '+g.errors.join(' • '));return old(g.text)};}
/* Last-line display protection: repeated model output is repaired before the teacher sees it. */
new MutationObserver(()=>{const o=document.getElementById('out');if(!o)return;const t=o.textContent||'';if(t.length>200){const c=clean(t);if(c!==t)o.textContent=c}}).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
})();
