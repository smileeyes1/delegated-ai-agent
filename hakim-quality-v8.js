/* HAKIM Ω Quality Gate v8 — additive fail-closed educational/math checks */
(function(){'use strict';
const E='٠١٢٣٤٥٦٧٨٩';
const n=s=>String(s??'').replace(/[٠-٩]/g,c=>E.indexOf(c));
function math(text,{maxResult,maxOperand}={}){const errors=[];for(const m of String(text||'').matchAll(/([٠-٩]+)\s*([+\-×÷])\s*([٠-٩]+)\s*=\s*([٠-٩]+)/g)){const a=+n(m[1]),b=+n(m[3]),r=+n(m[4]),op=m[2];const ok=op==='+'?a+b===r:op==='-'?a-b===r:op==='×'?a*b===r:op==='÷'&&b!==0&&a%b===0&&a/b===r;if(!ok)errors.push('MATH_EQUATION_ERROR:'+m[0]);if(maxResult!=null&&r>maxResult)errors.push('MATH_RESULT_OUT_OF_RANGE:'+m[0]);if(maxOperand!=null&&(a>maxOperand||b>maxOperand))errors.push('MATH_OPERAND_OUT_OF_RANGE:'+m[0])}return{ok:!errors.length,errors}}
function validate(text,opts={}){const t=String(text||''),errors=[];if(opts.grade===1&&opts.mathRange===10){const q=math(t,{maxResult:10,maxOperand:10});errors.push(...q.errors);if(/\b(ضرب|قسمة)\b/.test(t))errors.push('GRADE1_SCOPE_OPERATION_MISMATCH')}return{ok:!errors.length,errors}}
window.HAKIM_QUALITY_V8={validate,math};})();
