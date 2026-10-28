fetch('/api/state').then(r=>r.json()).then(s=>{document.getElementById('state').textContent=JSON.stringify(s,null,2)});
