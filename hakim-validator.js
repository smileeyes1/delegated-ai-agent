/* HAKIM Ω Validator v2 — deterministic educational + math QA */
(function(){'use strict';
const E='٠١٢٣٤٥٦٧٨٩';
function validateText(text,opts={}){const e=[],t=String(text||'').trim();if(!t)e.push('EMPTY_OUTPUT');if(t&&!/[\u0600-\u06ff]/.test(t))e.push('ARABIC_TEXT_MISSING');if(t.length<80&&opts.long)e.push('OUTPUT_TOO_SHORT');if(/TODO|TBD|lorem ipsum/i.test(t))e.push('PLACEHOLDER_CONTENT');if(/\b(api key|secret key|password)\b/i.test(t))e.push('SENSITIVE_CONTENT');if(/يقبل\s+٤/.test(t)&&/يأتي بعد\s+٢/.test(t))e.push('PEDAGOGICAL_SEQUENCE_WORDING_ERROR');return{ok:e.length===0,errors:e};}
function value(s){const n=String(s).replace(/[٠-٩]/g,c=>E.indexOf(c));return /^\d+$/.test(n)?Number(n):null;}
function validateMath(text){const e=[],t=String(text||'');if(/\d\s*[+×*÷\-]\s*\d\s*=\s*\d/.test(t))e.push('LATIN_NUMERALS_IN_MATH');for(const m of t.matchAll(/([٠-٩]+)\s*([+×*÷\-])\s*([٠-٩]+)\s*=\s*([٠-٩]+)/g)){const a=value(m[1]),op=m[2],b=value(m[3]),r=value(m[4]);let ok=true;if(op==='+')ok=a+b===r;if(op==='-')ok=a-b===r;if(op==='×')ok=a*b===r;if(op==='÷')ok=b!==0&&a%b===0&&a/b===r;if(!ok)e.push('MATH_EQUATION_ERROR:'+m[0]);}return{ok:e.length===0,errors:e};}
window.HAKIM_VALIDATOR={validateText,validateMath,validate(text,opts){const a=validateText(text,opts),b=validateMath(text);return{ok:a.ok&&b.ok,errors:[...a.errors,...b.errors],checkedAt:new Date().toISOString()}}};
})();
