/* HAKIM Ω Validator — deterministic educational QA */
(function(){'use strict';
 const ar=/[\u0600-\u06ff]/;
 function validateText(text,opts={}){const e=[],t=String(text||'').trim();if(!t)e.push('EMPTY_OUTPUT');if(t&&!ar.test(t))e.push('ARABIC_TEXT_MISSING');if(t.length<80&&opts.long)e.push('OUTPUT_TOO_SHORT');if(/TODO|TBD|lorem ipsum/i.test(t))e.push('PLACEHOLDER_CONTENT');if(/\b(api key|secret key|password)\b/i.test(t))e.push('SENSITIVE_PROMPT_CONTENT');return {ok:e.length===0,errors:e,checkedAt:new Date().toISOString()};}
 function validateMath(text){const e=[];const bad=/\d\s*[+×*\-]\s*\d\s*=\s*\d/.test(String(text||''));if(bad)e.push('USE_EASTERN_ARABIC_NUMERALS');if(/[٠-٩]\s*[+×*\-]\s*[٠-٩]\s*=/.test(String(text||''))){/* structural math accepted; visual renderer owns order */}return {ok:e.length===0,errors:e};}
 window.HAKIM_VALIDATOR={validateText,validateMath,validate(text,opts){const a=validateText(text,opts),b=validateMath(text);return {ok:a.ok&&b.ok,errors:[...a.errors,...b.errors],checkedAt:new Date().toISOString()};}};
})();
