const $ = id => document.getElementById(id);
const textUrl = 'https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf';
const visionBase = 'https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/f6d5376be1edb4d416d56da11e5397a961aca8ae/';
const labels = ['one','two','three','four','five','six'];
const worker = new Worker('./worker-bootstrap.js',{type:'module'});
const pending = new Map(); let nextId=1, ready=false, busy=false, report=null, loadSeconds=null;
function call(op,args={}) { return new Promise((resolve,reject)=>{const id=nextId++;pending.set(id,{resolve,reject});worker.postMessage({id,op,args});}); }
worker.addEventListener('message',({data})=>{
  if (data.type==='progress') {
    const p=data.progress||{}, value=Number.isFinite(p.progress)?Math.max(0,Math.min(100,p.progress)):0;
    $('load-progress').hidden=false;$('progress').value=value;$('progress-value').textContent=`${value.toFixed(1)}%`;
    $('progress-file').textContent=p.file||p.name||p.status||'Preparing model';return;
  }
  const request=pending.get(data.id);if(!request)return;pending.delete(data.id);data.ok?request.resolve(data.value):request.reject(Error(data.error));
});
worker.addEventListener('error',event=>{for(const request of pending.values())request.reject(Error(event.message||'Worker failed'));pending.clear();ready=false;setBusy(false);fail(event.message);});
function vision(){return ['receipt','receipt-us'].includes($('example').value);}
function setBusy(value){busy=value;for(const id of ['example','runtime','device','model-url','projector-url'])$(id).disabled=value||ready;$('load').disabled=value||ready;$('unload').disabled=value||!ready;$('generate').disabled=value||!ready;}
function fail(error){$('error').textContent=error?.message||String(error);$('error').hidden=false;$('status').textContent='Error';}
function clear(){ $('error').hidden=true;$('error').textContent=''; }
async function presets(){
  const name=$('example').value,isVision=vision();
  if(isVision)$('runtime').value='llamacpp';
  $('runtime').querySelector('[value="transformers"]').disabled=isVision;
  $('projector-controls').hidden=!isVision;$('text-controls').hidden=isVision;$('image-controls').hidden=!isVision;$('die-controls').hidden=name!=='fair-die';
  const uploaded=$('image').files[0];
  $('preview').hidden=!isVision||(!uploaded&&name!=='receipt');
  if(isVision&&!uploaded&&name==='receipt')$('preview').src='./typed-data/receipt/receipt.jpg';
  $('model-url').value=$('runtime').value==='transformers'?'onnx-community/Qwen3-0.6B-ONNX':isVision?visionBase+'Qwen3.5-2B-Q4_K_M.gguf':textUrl;
  $('projector-url').value=visionBase+'mmproj-F16.gguf';
  if(name==='fair-die'){
    $('context').value='A single roll of a fair die.';
    $('questions').value=JSON.stringify({roll:{type:'string',enum:labels,instructions:'What number will come up on a single roll of a fair six-sided die?',return_probabilities:true}},null,2);
  }else{
    const response=await fetch(isVision?`./typed-data/${name}/questions.json`:'./typed-data/fields.json');if(!response.ok)throw Error('Could not read example definitions');
    const data=await response.json();$('context').value=data.context||'Read the attached photo of a restaurant receipt.';$('questions').value=JSON.stringify(isVision?data:data.questions,null,2);
  }
  $('empty').hidden=false;$('result').hidden=true;$('save').disabled=true;report=null;
}
$('example').addEventListener('change',()=>presets().catch(fail));$('runtime').addEventListener('change',()=>presets().catch(fail));
$('image').addEventListener('change',()=>{const file=$('image').files[0];$('preview').hidden=!file;if(file){const previous=$('preview').dataset.url;if(previous)URL.revokeObjectURL(previous);const url=URL.createObjectURL(file);$('preview').src=url;$('preview').dataset.url=url;}});
$('load').addEventListener('click',async()=>{
  if(busy)return;clear();setBusy(true);$('status').textContent='Loading';$('load-progress').hidden=false;$('progress').value=0;
  try{
    if($('device').value==='webgpu'&&(!navigator.gpu||!await navigator.gpu.requestAdapter()))throw Error('WebGPU unavailable; select CPU explicitly.');
    const started=performance.now();
    const descriptor=await call('load',{model:$('model-url').value,runtimeModuleUrl:new URL('./runtime.js',import.meta.url).href,wasmModuleUrl:'https://cdn.jsdelivr.net/npm/@turbojev/wasm@0.31.0/turbojev_wasm.js',runtimeOptions:{backend:$('runtime').value,modality:vision()?'image':'text',device:$('device').value,dtype:'q4',nThreads:4,...($('runtime').value==='llamacpp'?{modelUrl:$('model-url').value,modelLabel:vision()?'Qwen3.5 2B':'Qwen3 0.6B',...(vision()?{mmprojUrl:$('projector-url').value}:{})}:{})}});
    loadSeconds=(performance.now()-started)/1000;
    ready=true;$('status').textContent='Ready';$('details').textContent=`${descriptor.name} · ${descriptor.modalities.join(', ')}`;$('load-progress').hidden=true;
  }catch(error){fail(error);}finally{setBusy(false);}
});
$('unload').addEventListener('click',async()=>{setBusy(true);try{await call('close');ready=false;$('status').textContent='Not loaded';}catch(error){fail(error);}finally{setBusy(false);}});
async function imageBytes(){const file=$('image').files[0];if(file)return file.arrayBuffer();if($('example').value==='receipt-us')throw Error('Choose your receipt photo first.');const response=await fetch('./typed-data/receipt/receipt.jpg');if(!response.ok)throw Error('Bundled receipt missing');return response.arrayBuffer();}
function base64(buffer){const bytes=new Uint8Array(buffer);let binary='';for(let offset=0;offset<bytes.length;offset+=32768)binary+=String.fromCharCode(...bytes.subarray(offset,offset+32768));return btoa(binary);}
$('generate').addEventListener('click',async()=>{
  if(!ready||busy)return;clear();setBusy(true);$('status').textContent='Generating';$('empty').hidden=true;$('result').hidden=true;$('save').disabled=true;
  report={example:$('example').value,package_version:'0.31.0',runtime:$('runtime').value,device:$('device').value,model:$('model-url').value,platform:navigator.userAgent,thinking:false,load_seconds:loadSeconds};
  try{
    let questions=JSON.parse($('questions').value);if(!questions||Array.isArray(questions)||typeof questions!=='object')throw Error('Field definitions must be a JSON object.');
    if(vision()&&$('fields').value.trim()){
      const names=new Set($('fields').value.split(',').map(s=>s.trim()));for(const name of names)if(!questions[name])throw Error(`Unknown field: ${name}`);
      for(const name of names)for(const dep of questions[name].depends_on||[]){if(!questions[dep])throw Error(`Missing dependency: ${dep}`);names.add(dep);}
      questions=Object.fromEntries(Object.entries(questions).filter(([name])=>names.has(name)));
    }
    let context=$('context').value;
    if(vision()){
      const bytes=await imageBytes();if(!bytes.byteLength||bytes.byteLength>24*2**20)throw Error('Photo must be nonempty and at most 24 MiB.');
      context={contract:'turbojev.media.v1',modality:'image',text:'Read the attached photo of a restaurant receipt.',base64:base64(bytes)};
      report.image_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),byte=>byte.toString(16).padStart(2,'0')).join('');
      report.mmproj=$('projector-url').value;report.subset=Boolean($('fields').value.trim());
    }
    const request={context,questions,thinking:false,text_max_tokens:64,numeric_max_tokens:64};report.fields=Object.keys(questions);
    if($('example').value==='fair-die'){
      const budget=$('budget').value;request.seed=42;questions.roll.permutations=/^\d+$/.test(budget)?Number(budget):budget;report.permutations=questions.roll.permutations;
    }
    const started=performance.now();report.response=await call('generate',{request});report.evaluation_seconds=(performance.now()-started)/1000;
    if($('example').value==='fair-die'){
      const probabilities=report.response.result.roll.probabilities,values=labels.map(label=>probabilities[label]);
      if(values.some(p=>!Number.isFinite(p)||p<0||p>1)||Math.abs(values.reduce((a,b)=>a+b,0)-1)>1e-9)throw Error('Invalid model distribution');
      report.kl_uniform_to_prediction=values.every(p=>p>0)?values.reduce((sum,p)=>sum+Math.log((1/6)/p)/6,0):null;
    }
    report.ok=true;report.error=null;$('result').textContent=JSON.stringify(report,null,2);$('result').hidden=false;$('elapsed').textContent=`${report.evaluation_seconds.toFixed(3)}s`;$('status').textContent='Ready';
  }catch(error){report.ok=false;report.error=error.message;fail(error);}finally{$('save').disabled=false;setBusy(false);}
});
$('save').addEventListener('click',()=>{if(!report)return;const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=`result-${report.example}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
presets().catch(fail);
