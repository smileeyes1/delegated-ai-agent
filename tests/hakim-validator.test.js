const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('hakim-validator.js','utf8'),ctx);
const V=ctx.window.HAKIM_VALIDATOR;
function pass(s){const r=V.validate(s,{long:true});assert.equal(r.ok,true,JSON.stringify(r.errors));}
function fail(s){const r=V.validate(s,{long:true});assert.equal(r.ok,false,'Expected NO-GO');return r.errors;}
pass('درس العدد ٥\nالهدف التعليمي: يتعرف الطالب على العدد ٥.\nالنشاط: يعد خمس بطاقات ويطابقها مع الرمز ٥.\nالتقييم: يختار الطالب بطاقة العدد ٥ من بين ثلاث بطاقات.');
assert(fail('درس العدد ٤\nالهدف التعليمي: يتعرف الطالب على العدد ٤.\nالنشاط: نشاط رئيسي بسيط.\nالنشاط: نشاط آخر.').some(x=>x==='MULTIPLE_MAIN_ACTIVITIES'));
assert(fail('درس العدد ٤\nالهدف التعليمي: يتعرف الطالب على العدد ٤.\nالنشاط: يعد أربع صور.\nالملخص النهائي: تعلمنا العدد ٤.\nالملخص النهائي: انتهى الدرس.').some(x=>x==='MULTIPLE_SUMMARIES'));
assert(fail('درس العدد ٣\nالهدف التعليمي: يتعرف الطالب على العدد ٣.\nالنشاط: يتعلم العدد ٣.\nالملخص: العدد ٣.\nيأتي بعد ٢ ويقبل ٤.').some(x=>x==='PEDAGOGICAL_SEQUENCE_WORDING_ERROR'));
assert(fail('درس العدد ٣\nالهدف التعليمي: يتعرف الطالب على العدد ٣.\nالنشاط: ٣ + ٤ = ٨\nالتقييم: يختار ٣.').some(x=>x.startsWith('MATH_EQUATION_ERROR')));
assert(fail('درس العدد ٣\nالهدف التعليمي: يتعرف الطالب على العدد ٣.\nالنشاط: ٣ + ٤ = □\nالتقييم: يختار ٣.').some(x=>x.startsWith('MATH_VISUAL_ORDER_REQUIRES_EXPLICIT_TRANSFORM')));
assert(fail('lesson 123\nTODO').some(x=>x==='ARABIC_TEXT_MISSING'||x==='PLACEHOLDER_CONTENT'));
console.log('HAKIM Ω validator adversarial regression: PASS');
