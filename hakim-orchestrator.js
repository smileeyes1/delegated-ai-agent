/* HAKIM Ω Orchestrator v1 — autonomous quality recovery */
(function(){'use strict';
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function normalize(s){return String(s||'').replace(/\r/g,'').replace(/\n{3,}/g,'\n\n').trim()}
function isCritical(errs){return (errs||[]).some(e=>/MATH_|SENSITIVE|ARABIC_TEXT|EMPTY|OUTPUT_TOO|REPETITIVE|MULTIPLE_|EXTRA_|ADVANCED_|PLACEHOLDER/.test(e))}
function repairPrompt(original,errors){return `أنت طبقة إصلاح جودة في HAKIM Ω. أصلح المورد التالي فقط بناءً على الأخطاء المحددة. أعد المورد كاملًا مرة واحدة بعد الإصلاح، بلا شرح ولا اعتذار ولا تكرار. حافظ على الغاية والصف والسياق. ${errors.join('، ')}\n\nالمورد:\n${original}`}
async function recover(text,askFn,opts={}){
 let current=normalize(text),history=[];
 for(let pass=1;pass<=2;pass++){
  const g=window.HAKIM_VALIDATOR.validate(current,{long:true});
  history.push({pass,ok:g.ok,errors:g.errors,repaired:g.repaired});
  if(g.ok)return {ok:true,text:g.text,history};
  if(!isCritical(g.errors)||!askFn)break;
  await wait(120);
  const candidate=await askFn(repairPrompt(current,g.errors),true);
  if(!candidate||normalize(candidate)===current)break;
  current=normalize(candidate);
 }
 const final=window.HAKIM_VALIDATOR.validate(current,{long:true});
 history.push({pass:history.length+1,ok:final.ok,errors:final.errors,repaired:final.repaired});
 return {ok:final.ok,text:final.text,history};
}
window.HAKIM_ORCHESTRATOR={recover};
})();
