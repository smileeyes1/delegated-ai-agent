/* deterministic regression smoke for HAKIM_QUALITY_V8 */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const code=fs.readFileSync('hakim-quality-v8.js','utf8');
const ctx={};vm.createContext(ctx);vm.runInContext(code,ctx);
const V=ctx.HAKIM_QUALITY_V8;
assert.equal(V.validate('٣ + ٥ = ٨',{grade:1,mathRange:10}).ok,true);
assert.equal(V.validate('٧ + ٢ = ٩',{grade:1,mathRange:10}).ok,true);
assert.equal(V.validate('١٠ + ١ = ١١',{grade:1,mathRange:10}).ok,false);
assert.equal(V.validate('٣ + ٥ = ٩',{grade:1,mathRange:10}).ok,false);
assert.equal(V.validate('درس العدد ٥\nالضرب والقسمة',{grade:1,mathRange:10}).ok,false);
console.log('QUALITY_GATE_V8=PASS');
