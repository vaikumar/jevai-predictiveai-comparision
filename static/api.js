// Endpoint URLs are supplied by service_urls.json through the dashboard.
const configReady=fetch('/api/config').then(async r=>{if(!r.ok)throw Error('Cannot load service URLs');return r.json()});
async function request(base,path,data,method='POST'){
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),path==='benchmark'?2700000:30000);
  try{
    const r=await fetch(base+'/api/'+path,{method,signal:controller.signal,headers:{'Content-Type':'application/json'},...(data!==undefined?{body:JSON.stringify(data)}:{})});
    const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));return d;
  }finally{clearTimeout(timeout)}
}
async function invoke(base,path,body){
  try{return await request(base,path,body)}catch(e){return {status:'error',error:path+' service: '+e.message,latency_ms:null}}
}
export async function api(path,data,method='POST'){
  const urls=await configReady;
  if(path==='compare'){
    const [xgboost,jev]=await Promise.all([invoke(urls.predictive,'predict',data),invoke(urls.jev,'jev',data)]);
    return {request:data,xgboost,jev};
  }
  if(path==='status'){
    const [p,j]=await Promise.allSettled([request(urls.predictive,'status',undefined,'GET'),request(urls.jev,'status',undefined,'GET')]);
    return {training:p.status==='fulfilled'?p.value.training:{accuracy:null},jev_configured:j.status==='fulfilled'&&j.value.jev_configured,service_errors:[p,j].filter(v=>v.status==='rejected').map(v=>v.reason.message)};
  }
  return request(path==='settings'?urls.jev:urls.dashboard,path,data,method);
}
export async function endpointSummary(){const c=await configReady;return 'Predictive: '+c.predictive+' · JEV: '+c.jev+' · Dashboard: '+c.dashboard}
