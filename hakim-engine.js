/* HAKIM Ω Resource Engine — browser-first, zero-install artifact generation */
(function(){
  'use strict';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const slug=s=>String(s||'hakim-resource').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,'-').replace(/^-|-$/g,'').slice(0,70)||'hakim-resource';
  const num=n=>String(n).replace(/\d/g,d=>'٠١٢٣٤٥٦٧٨٩'[d]);
  function lessonFromText(text){
    const title=(text.match(/(?:درس|عنوان)\s*(?:العدد|عن)?\s*([^\n#]+)/i)||[])[1]||'مورد تعليمي';
    return {schema:'HAKIM-RESOURCE/1.0',type:'lesson_pack',title:title.trim(),language:'ar',direction:'rtl',content:text,createdAt:new Date().toISOString()};
  }
  function validate(x){
    const errors=[];
    if(!x||!x.content) errors.push('المحتوى فارغ');
    if(x.direction!=='rtl') errors.push('اتجاه العربية يجب أن يكون RTL');
    if(x.type==='lesson_pack'&&x.content.length<80) errors.push('المحتوى قصير جدًا لمورد تعليمي كامل');
    return {ok:errors.length===0,errors};
  }
  function interactiveHtml(resource){
    const title=esc(resource.title); const content=esc(resource.content);
    return `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>body{font-family:system-ui,sans-serif;margin:0;background:#f5f7fa;color:#17202a}main{max-width:900px;margin:auto;padding:24px}article{background:white;border:1px solid #e1e6eb;border-radius:20px;padding:24px;white-space:pre-wrap;line-height:1.8}button{padding:12px 18px;border:0;border-radius:12px;font:inherit;background:#111827;color:white;margin-bottom:16px}@media print{button{display:none}body{background:white}main{max-width:none;padding:0}article{border:0}}</style></head><body><main><button onclick="window.print()">طباعة / حفظ PDF</button><article><h1>${title}</h1>${content}</article></main></body></html>`;
  }
  function download(name,data,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
  window.HAKIM_ENGINE={
    build(text){const r=lessonFromText(text);const v=validate(r);if(!v.ok)throw new Error(v.errors.join(' • '));return r},
    exportHtml(r){download(slug(r.title)+'.html',interactiveHtml(r),'text/html;charset=utf-8')},
    exportJson(r){download(slug(r.title)+'.json',JSON.stringify(r,null,2),'application/json;charset=utf-8')},
    exportText(r){download(slug(r.title)+'.txt',r.content,'text/plain;charset=utf-8')},
    printPdf(r){const w=window.open('','_blank');if(!w)throw new Error('POPUP_BLOCKED');w.document.open();w.document.write(interactiveHtml(r));w.document.close();setTimeout(()=>w.print(),350)},
    validate
  };
})();
