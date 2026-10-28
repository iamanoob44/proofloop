'use strict';
let state, selectedRevision, selectedRun, busy=false;
const $=id=>document.getElementById(id);
const pretty=x=>JSON.stringify(x,null,2);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const badge=s=>el('span',s.replaceAll('_',' '),'badge '+s);
function message(text,error=false){$('message').textContent=text;$('message').className=error?'error':'';}
async function api(path,body){const r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-ProofLoop':'1'},body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw Error(v.error||'Request failed');return v;}
async function refresh(){const r=await fetch('/api/state');if(!r.ok)throw Error('Unable to load saved evidence');state=await r.json();render();}
async function action(fn){if(busy)return;busy=true;document.querySelectorAll('button').forEach(b=>b.disabled=true);message('Working…');try{await fn();await refresh();}catch(e){message(e.message,true);}finally{busy=false;render();}}
function button(text,fn,cls=''){const b=el('button',text,cls);b.disabled=busy;b.addEventListener('click',()=>action(fn));return b;}
function reviewer(){const v=$('reviewer').value.trim();if(!v)throw Error('Enter the reviewer/editor identity.');return v;}
function note(){const v=$('review-note').value.trim();if(!v)throw Error('Add a requirement-grounded review reason.');return v;}
function latest(){const map=new Map();for(const r of state.revisions)map.set(r.test_id,r);return [...map.values()];}
function rawDetails(title,value){const d=el('details');d.append(el('summary',title),el('pre',pretty(value)));return d;}
function unchanged(r){if(pretty(JSON.parse($('test-json').value))!==pretty(r.test))throw Error('Save your edits as a new revision before approval or execution.');}
function render(){if(!state)return;$('source').textContent='Source '+state.source.git_revision.slice(0,8)+' · '+state.source.source_hash.slice(0,8);$('spec').textContent=state.spec;$('generate').disabled=busy;$('export').disabled=busy;
 const list=latest();if(!selectedRevision&&list.length)selectedRevision=list[0].id;$('review-count').textContent=list.length+' tests · '+state.revisions.length+' revisions';
 $('proposals').replaceChildren();if(!list.length)$('proposals').append(el('p','Load proposals to begin.','empty'));
 for(const r of list){const b=button('',async()=>{selectedRevision=r.id;message('Inspect the requirement, inputs, expectation and rationale.');});b.className=r.id===selectedRevision?'selected':'';b.append(el('strong',r.test.title),el('small',r.test.requirement_refs.join(' · ')+' / revision '+r.number),badge(r.status));$('proposals').append(b);}
 const r=state.revisions.find(r=>r.id===selectedRevision);if(r)renderEditor(r);
 renderGenerations();renderRuns();
}
function renderEditor(r){const box=$('editor-panel');box.replaceChildren(el('h3',r.test.title));box.append(badge(r.status),badge(r.provenance.mode),el('p',r.test.rationale,'rationale'));
 box.append(el('p','Revision '+r.number+' · '+r.id+' · fixture '+r.test.fixture,'hint'));
 const label=el('label','Structured proposal — edit inputs, expected response, or rationale');const area=el('textarea');area.id='test-json';area.spellcheck=false;area.value=pretty(r.test);label.append(area);box.append(label);
 const buttons=el('div',undefined,'actions');buttons.append(button('Save new revision',async()=>{const test=JSON.parse(area.value);const v=await api('edit',{revision_id:r.id,test,editor:reviewer()});selectedRevision=v.id;message('New revision saved. Approval reset to pending.');}),
 button('Approve',async()=>{unchanged(r);await api('review',{revision_id:r.id,status:'approved',reviewer:reviewer(),note:note()});message('Revision approved.');},'primary'),
 button('Reject',async()=>{unchanged(r);await api('review',{revision_id:r.id,status:'rejected',reviewer:reviewer(),note:note()});message('Revision rejected; execution blocked.');}),
 button('Execute approved revision',async()=>{unchanged(r);const run=await api('run',{revision_id:r.id});selectedRun=run.id;message('Execution: '+run.outcome.replaceAll('_',' '));},'primary'));
 buttons.lastChild.disabled=busy||r.status!=='approved';box.append(buttons);
 box.append(rawDetails('Revision and review history', {revisions:state.revisions.filter(x=>x.test_id===r.test_id),reviews:state.reviews.filter(e=>state.revisions.some(x=>x.test_id===r.test_id&&x.id===e.revision_id))}));
}
function renderGenerations(){$('generation-count').textContent='('+state.generations.length+')';const box=$('generations');box.replaceChildren();for(const g of [...state.generations].reverse()){const row=el('div',undefined,'generation');row.append(badge(g.mode),badge(g.status),el('span',`${g.schema_valid}/${g.proposals} schema valid · ${g.duration_ms} ms`));row.append(el('p',g.error||g.label||('Model: '+g.model)));row.append(rawDetails('Inspect prompt, output and attempt identity',g));if(g.mode==='live'&&g.status==='error')row.append(button('Retry as a new attempt',async()=>{const result=await api('generate',{mode:'live',focus:g.input.focus,parent_generation_id:g.id});message(result.generation.error||'New attempt generated.',result.generation.status==='error');}));box.append(row);}}
function renderRuns(){const box=$('runs');box.replaceChildren();if(!state.runs.length){box.append(el('p','No executions yet. Approve a revision, then execute it.','empty'));$('run-detail').replaceChildren();return;}
 const wrap=el('div',undefined,'table-wrap'),table=el('table'),head=el('tr');for(const t of ['Attempt','Test / revision','Outcome','Source','Previous attempt'])head.append(el('th',t));table.append(head);
 for(const run of [...state.runs].reverse()){const row=el('tr'),id=el('td');id.append(button(run.id.slice(0,8),async()=>{selectedRun=run.id;message('Inspecting saved attempt.');},'run-button'));row.append(id,el('td',run.revision.test.title+' / v'+run.revision.number));const status=el('td');status.append(badge(run.outcome));row.append(status,el('td',run.source.git_revision.slice(0,8)),el('td',run.parent_run_id?run.parent_run_id.slice(0,8):'—'));table.append(row);}wrap.append(table);box.append(wrap);
 const run=state.runs.find(r=>r.id===selectedRun)||state.runs.at(-1);selectedRun=run.id;const detail=$('run-detail');detail.replaceChildren(el('h3','Attempt '+run.id.slice(0,8),'run-title'));detail.append(el('p',run.created_at+' · '+run.duration_ms+' ms · '+run.target,'hint'));
 if(run.parent_run_id){const old=state.runs.find(r=>r.id===run.parent_run_id);if(old){const comparison=el('div',undefined,'compare');for(const [name,value] of [['Original',old],['Retest',run]]){const col=el('div');col.append(el('strong',name+' · '+value.id.slice(0,8)),el('p','Same revision '+value.revision_id.slice(0,8)),badge(value.outcome));comparison.append(col);}detail.append(comparison);}}
 if(run.error)detail.append(el('p',run.error,'rationale'));if(run.inconsistent_result)detail.append(el('p',run.investigation_note,'rationale'));
 const grid=el('div',undefined,'table-wrap'),table2=el('table'),h=el('tr');['Assertion','Expected','Actual','Observation'].forEach(t=>h.append(el('th',t)));table2.append(h);for(const a of run.assertions){const row=el('tr');row.append(el('td',a.field));for(const v of [a.expected,a.actual]){const cell=el('td');cell.append(el('pre',pretty(v)));row.append(cell);}row.append(el('td',a.passed?'Match':'Mismatch'));table2.append(row);}grid.append(table2);detail.append(grid);
 detail.append(button('Retest exact revision',async()=>{const next=await api('run',{revision_id:run.revision_id,parent_run_id:run.id});selectedRun=next.id;message('Retest saved; original attempt retained.');}));
 const diagnosis=el('div',undefined,'form-row'),label=el('label','Reviewer diagnosis'),select=el('select');select.id='diagnosis';for(const value of ['inconclusive','product_defect','incorrect_test','environment']){const o=el('option',value.replaceAll('_',' '));o.value=value;select.append(o);}label.append(select);diagnosis.append(label,button('Record diagnosis',async()=>{await api('diagnose',{run_id:run.id,classification:select.value,reviewer:reviewer(),note:note()});message('Diagnosis appended separately from execution outcome.');}));detail.append(diagnosis);
 detail.append(rawDetails('Full reproducible record and reviewer diagnoses',{run,diagnoses:state.diagnoses.filter(d=>d.run_id===run.id)}));
}
$('mode').addEventListener('change',()=>{const live=$('mode').value==='live';$('generate').textContent=live?'Generate with provider':'Load proposals';$('mode-note').textContent=live?'Sends the fictional specification and focus to OpenAI. Requires server-side credentials. No silent fallback.':$('mode').value==='offline'?'Prepared assistant-authored examples. No live model call.':'Deliberately incorrect teaching example. Not an observed model mistake.';});
$('generate').addEventListener('click',()=>action(async()=>{const result=await api('generate',{mode:$('mode').value,focus:$('focus').value});if(result.revisions.length)selectedRevision=result.revisions[0].id;message(result.generation.error||result.revisions.length+' proposals loaded. Review before execution.',result.generation.status==='error');}));
$('export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([pretty(state)],{type:'application/json'}));const a=el('a');a.href=url;a.download='proofloop-evidence.json';a.click();URL.revokeObjectURL(url);});
refresh().then(()=>message('Workspace ready. Select a proposal source.')).catch(e=>message(e.message,true));
