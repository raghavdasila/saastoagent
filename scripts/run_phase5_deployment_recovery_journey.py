from __future__ import annotations
import argparse,asyncio,json,secrets,shutil,subprocess,time
from datetime import UTC,datetime
from pathlib import Path
from urllib.parse import urlsplit
from playwright.async_api import Response,async_playwright
from run_phase5_builder_lifecycle_journey import RESET_CODE,_capture,_maximize,_submit_sign_in

ROOT=Path(__file__).resolve().parents[1];ARTIFACT_ROOT=ROOT/'artifacts'/'phase5-deployment-recovery';CONTAINER='corpus-development-backend-1'
OWNER_EMAIL='horizontal-f644228a58384de4a067adde260c1f6a@example.com';ORGANIZATION_ID='04abb0ca49c34af0a181e010c995f5e7';AGENT_ID='1f99c29b0097436eaf590dd6d0966ebf';AGENT_NAME='Shopping assistant';CHANNEL_ID='c7104231cf7d428aaf312710f803b26a';ORIGINAL='272f3f43bdfc4fc5a5dc500083ef0dc8';ALTERNATE='9b50ebab136749d09d1a334ad763136a'
def arguments():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:5199');p.add_argument('--headed',action='store_true');return p.parse_args()
def _reset(password):
 d=subprocess.run(['docker','exec','-i','-w','/workspace/corpus/backend',CONTAINER,'python','-c',RESET_CODE,OWNER_EMAIL,AGENT_ID,ORGANIZATION_ID],input=password,text=True,capture_output=True,timeout=60)
 if d.returncode:raise RuntimeError('Exact deployment owner unavailable.')
 return json.loads(d.stdout)
def _state():
 code=r"""
import sqlite3,json,sys
org,channel=sys.argv[1:];c=sqlite3.connect('/var/lib/corpus/corpus.sqlite3');c.row_factory=sqlite3.Row
ch=c.execute("select id,enabled,active_deployment_id from agent_channels where replace(lower(organization_id),'-','')=? and replace(lower(id),'-','')=?",(org,channel)).fetchone();ds=c.execute("select id,build_id,status,bundle_hash,runtime_deployment_id from agent_deployments where replace(lower(organization_id),'-','')=? and replace(lower(channel_id),'-','')=? order by created_at",(org,channel)).fetchall();print(json.dumps({'channel':dict(ch) if ch else None,'deployments':[dict(x) for x in ds]}))
"""
 d=subprocess.run(['docker','exec','-i','-w','/workspace/corpus/backend',CONTAINER,'python','-c',code,ORGANIZATION_ID.replace('-',''),CHANNEL_ID.replace('-','')],text=True,capture_output=True,timeout=30)
 if d.returncode:raise RuntimeError('Exact deployment state unavailable.')
 return json.loads(d.stdout)
async def _restart(url):
 d=subprocess.run(['docker','restart',CONTAINER],capture_output=True,text=True,timeout=120)
 if d.returncode:raise RuntimeError('Backend restart failed.')
 import urllib.request
 for _ in range(90):
  try:
   if urllib.request.urlopen(url+'/readyz',timeout=2).status==200:return
  except Exception:pass
  await asyncio.sleep(1)
 raise RuntimeError('Backend did not recover after restart.')
async def run(args):
 run_id=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4);directory=ARTIFACT_ROOT/run_id;videos=directory/'raw-video';videos.mkdir(parents=True);shots=[];ops=[];diagnostics={'httpErrors':[],'consoleErrors':[],'pageErrors':[]};before=_state();after=None;password='Corpus-Deploy-'+secrets.token_urlsafe(24)+'!9';destroy='Corpus-Deploy-Destroy-'+secrets.token_urlsafe(24)+'!9';browser=context=page=None;video=None;error=None;recovered=False;tasks=set();start=time.monotonic()
 async def observe(r:Response):
  path=urlsplit(r.url).path;expected=path.startswith('/api/routedeck/reviews/') and path.endswith('/reject') and r.status==409
  if r.status>=400 and not expected:diagnostics['httpErrors'].append({'method':r.request.method,'path':path,'status':r.status})
  if r.status==200 and r.request.method=='POST' and path=='/api/routedeck/dispatch':
   try:
    b=await r.json();op=b.get('operation_id')
    if op:ops.append({'operationId':op,'disposition':b.get('disposition'),'outcome':b.get('outcome')})
   except Exception:pass
 def schedule(r):
  t=asyncio.create_task(observe(r));tasks.add(t);t.add_done_callback(tasks.discard)
 try:
  if before['channel']['active_deployment_id'].replace('-','')!=ORIGINAL.replace('-','') or len(before['deployments'])!=2 or any(x['status']!='ready' for x in before['deployments']):raise RuntimeError('Retained rollback preflight changed.')
  identity=_reset(password);recovered=True
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=not args.headed);context=await browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=videos,record_video_size={'width':1440,'height':1000});page=await context.new_page();page.on('response',schedule);page.on('console',lambda i:diagnostics['consoleErrors'].append({'type':i.type,'text':i.text}) if i.type in {'warning','error'} else None);page.on('pageerror',lambda i:diagnostics['pageErrors'].append({'message':str(i)}))
   await page.goto(args.url);await page.get_by_role('heading',name='Explore Corpus',exact=True).wait_for(timeout=30_000);await page.get_by_role('button',name='Sign in',exact=True).click();await page.get_by_role('heading',name='Sign in',exact=True).wait_for();await _submit_sign_in(page,identity['email'],password);await page.get_by_label('Sign out',exact=True).wait_for(timeout=30_000);await page.locator('section.workspace-home').get_by_role('button',name='Open Agents',exact=True).click();agents=page.locator('section.agents-home');await agents.locator('#agents-home-title').wait_for(timeout=30_000);agent=agents.get_by_label('Agent inventory').get_by_role('button').filter(has_text=AGENT_NAME);await agent.wait_for(state='visible',timeout=30_000);await agent.click();button=agents.get_by_role('button',name='Channels',exact=True)
   for _ in range(120):
    if await button.is_enabled():break
    await page.wait_for_timeout(250)
   await button.click();surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page);history=surface.get_by_role('heading',name='Deployment history',exact=True).locator('..');await surface.get_by_text('Active deployment',exact=True).wait_for();await _capture(page,directory,'01-two-immutable-releases',shots)
   rollback=surface.get_by_role('button',name='Review rollback to this version',exact=True);await rollback.click();review=page.locator('section.deployment-review');await review.get_by_role('heading',name='Approve hosted Agent rollback',exact=True).wait_for();await _capture(page,directory,'02-rollback-review',shots);await review.get_by_role('button',name='Keep current deployment',exact=True).click();await review.wait_for(state='detached');
   await rollback.click();review=page.locator('section.deployment-review');await review.get_by_role('button',name='Roll back to reviewed deployment',exact=True).click();await review.wait_for(state='detached');
   for _ in range(120):
    if _state()['channel']['active_deployment_id'].replace('-','')==ALTERNATE.replace('-',''):break
    await page.wait_for_timeout(250)
   await page.reload(wait_until='domcontentloaded');surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page);await _capture(page,directory,'03-alternate-release-active',shots)
   await _restart('http://127.0.0.1:8099');await page.reload(wait_until='domcontentloaded');surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page);await _capture(page,directory,'04-active-release-after-restart',shots)
   rollback=surface.get_by_role('button',name='Review rollback to this version',exact=True);await rollback.click();review=page.locator('section.deployment-review');await review.get_by_role('button',name='Roll back to reviewed deployment',exact=True).click();await review.wait_for(state='detached');
   for _ in range(120):
    if _state()['channel']['active_deployment_id'].replace('-','')==ORIGINAL.replace('-',''):break
    await page.wait_for_timeout(250)
   await page.reload(wait_until='domcontentloaded');surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page);await _capture(page,directory,'05-original-release-restored',shots);after=_state()
   if tasks:await asyncio.gather(*tuple(tasks),return_exceptions=True)
   if after!=before:raise RuntimeError('Original active deployment was not restored exactly.')
   required=['deployment.rollback']*3;cursor=0
   for op in [x['operationId'] for x in ops]:
    if cursor<len(required) and op==required[cursor]:cursor+=1
   if cursor!=3:raise RuntimeError('Exact reviewed rollback sequence not observed.')
   unexpected=[x for x in diagnostics['consoleErrors'] if '409' not in x['text']]
   if diagnostics['httpErrors'] or diagnostics['pageErrors'] or unexpected:raise RuntimeError('Deployment interval has unexpected diagnostics.')
 except Exception as e:error=f'{type(e).__name__}: {e}'
 finally:
  if page is not None:
   try:
    raw=page.video
    if raw is not None:await page.close();video=Path(await raw.path())
   except Exception:pass
  if context is not None:
   try:await context.close()
   except Exception:pass
  if browser is not None:
   try:await browser.close()
   except Exception:pass
  if recovered:
   try:_reset(destroy)
   except Exception as e:error=error or str(e)
 if video and video.is_file():final=directory/'phase5-deployment-recovery-normal-speed.webm';video.replace(final);video=final
 result={'runId':run_id,'status':'passed' if error is None else 'failed','scope':'isolated Phase 5 deployment rollback and restart recovery','before':before,'after':after,'operations':ops,'screenshots':shots,'video':None if not video else str(video.relative_to(ROOT)),'videoMetadata':{'playbackRate':1.0,'width':1440,'height':1000,'maximizedSurface':True},'diagnostics':diagnostics,'elapsedSeconds':round(time.monotonic()-start,3),'error':error};path=directory/'result.json';path.write_text(json.dumps(result,indent=2)+'\n')
 for f in directory.rglob('*'):
  if f.is_file() and (password.encode() in f.read_bytes() or destroy.encode() in f.read_bytes()):shutil.rmtree(directory);raise RuntimeError('Credential canary reached deployment evidence.')
 print(f'run={run_id} status={result["status"]}\nartifact={path}\nvideo={result["video"]}');
 if error:print('error='+error)
 return 0 if error is None else 1
async def main():
 async with asyncio.timeout(13*60):return await run(arguments())
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
