from __future__ import annotations

import argparse, asyncio, json, secrets, shutil, subprocess, time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Response, async_playwright
from run_phase5_builder_lifecycle_journey import RESET_CODE, _capture, _maximize, _submit_sign_in

ROOT=Path(__file__).resolve().parents[1]; ARTIFACT_ROOT=ROOT/'artifacts'/'phase5-channel-availability'; CONTAINER='corpus-development-backend-1'
OWNER_EMAIL='horizontal-f644228a58384de4a067adde260c1f6a@example.com'; ORGANIZATION_ID='04abb0ca49c34af0a181e010c995f5e7'; AGENT_ID='1f99c29b0097436eaf590dd6d0966ebf'; AGENT_NAME='Shopping assistant'
CHANNEL_ID='c7104231cf7d428aaf312710f803b26a'; CHANNEL_NAME='Store Taxonomy'; SLUG='store-taxonomy-5b1edb'; DEPLOYMENT_ID='272f3f43bdfc4fc5a5dc500083ef0dc8'

def arguments():
    p=argparse.ArgumentParser(description='Record isolated hosted Web availability lifecycle.');p.add_argument('--url',default='http://127.0.0.1:5199');p.add_argument('--headed',action='store_true');return p.parse_args()

def _owner_reset(password:str):
    done=subprocess.run(['docker','exec','-i','-w','/workspace/corpus/backend',CONTAINER,'python','-c',RESET_CODE,OWNER_EMAIL,AGENT_ID,ORGANIZATION_ID],input=password,text=True,capture_output=True,timeout=60,check=False)
    if done.returncode!=0:raise RuntimeError('The exact Channel owner could not be recovered.')
    return json.loads(done.stdout.strip())

def _state():
    code=r"""
import json,sqlite3,sys
org,agent,channel,deployment=sys.argv[1:];c=sqlite3.connect('/var/lib/corpus/corpus.sqlite3');c.row_factory=sqlite3.Row
row=c.execute('''select id,agent_id,slug,status,enabled,active_deployment_id,runtime_channel_id from agent_channels where replace(lower(organization_id),'-','')=? and replace(lower(agent_id),'-','')=? and replace(lower(id),'-','')=?''',(org,agent,channel)).fetchone()
dep=c.execute('''select id,build_id,status,bundle_hash,runtime_deployment_id from agent_deployments where replace(lower(organization_id),'-','')=? and replace(lower(id),'-','')=?''',(org,deployment)).fetchone();print(json.dumps({'channel':dict(row) if row else None,'deployment':dict(dep) if dep else None}));c.close()
"""
    done=subprocess.run(['docker','exec','-w','/workspace/corpus/backend',CONTAINER,'python','-c',code,ORGANIZATION_ID.replace('-',''),AGENT_ID.replace('-',''),CHANNEL_ID.replace('-',''),DEPLOYMENT_ID.replace('-','')],text=True,capture_output=True,timeout=30,check=False)
    if done.returncode!=0:raise RuntimeError('The exact Channel state is unavailable.')
    return json.loads(done.stdout)

async def run(args):
    run_id=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4);directory=ARTIFACT_ROOT/run_id;videos=directory/'raw-video';videos.mkdir(parents=True)
    shots=[];operations=[];diagnostics={'httpErrors':[],'consoleErrors':[],'pageErrors':[],'requestFailures':[]};before=_state();after=None
    password='Corpus-Channel-'+secrets.token_urlsafe(24)+'!9';destroy='Corpus-Channel-Destroy-'+secrets.token_urlsafe(24)+'!9';browser=context=page=None;video_path=None;error=None;recovered=False;tasks=set();started=time.monotonic();public_status={}
    async def observe(response:Response):
        path=urlsplit(response.url).path;expected=path.startswith('/api/routedeck/reviews/') and path.endswith('/reject') and response.status==409
        if response.status>=400 and not expected and not (path==f'/api/public/agents/{SLUG}/sessions' and response.status==503):diagnostics['httpErrors'].append({'method':response.request.method,'path':path,'status':response.status})
        if response.status==200 and response.request.method=='POST' and path=='/api/routedeck/dispatch':
            try:
                body=await response.json();op=body.get('operation_id') or body.get('operationId')
                if isinstance(op,str):operations.append({'operationId':op,'disposition':body.get('disposition'),'outcome':body.get('outcome')})
            except Exception:pass
    def schedule(response):
        task=asyncio.create_task(observe(response));tasks.add(task);task.add_done_callback(tasks.discard)
    try:
        if before['channel'] is None or before['channel']['enabled']!=1 or before['channel']['active_deployment_id'].replace('-','')!=DEPLOYMENT_ID.replace('-','') or before['deployment']['status']!='ready':raise RuntimeError('The retained active hosted Channel preflight changed.')
        identity=_owner_reset(password);recovered=True
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=not args.headed);context=await browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=videos,record_video_size={'width':1440,'height':1000});page=await context.new_page();page.on('response',schedule)
            page.on('console',lambda i:diagnostics['consoleErrors'].append({'type':i.type,'text':i.text}) if i.type in {'warning','error'} else None);page.on('pageerror',lambda i:diagnostics['pageErrors'].append({'message':str(i)}));page.on('requestfailed',lambda r:diagnostics['requestFailures'].append({'method':r.method,'path':urlsplit(r.url).path,'failure':r.failure}))
            await page.goto(args.url);await page.get_by_role('heading',name='Explore Corpus',exact=True).wait_for(timeout=30_000);await page.get_by_role('button',name='Sign in',exact=True).click();await page.get_by_role('heading',name='Sign in',exact=True).wait_for();await _submit_sign_in(page,identity['email'],password);await page.get_by_label('Sign out',exact=True).wait_for(timeout=30_000)
            await page.locator('section.workspace-home').get_by_role('button',name='Open Agents',exact=True).click();agents=page.locator('section.agents-home');await agents.locator('#agents-home-title').wait_for(timeout=30_000);agent=agents.get_by_label('Agent inventory').get_by_role('button').filter(has_text=AGENT_NAME);await agent.wait_for(state='visible',timeout=30_000)
            if await agent.count()!=1:raise RuntimeError('The exact Channel Agent is unavailable or ambiguous.')
            await agent.click();button=agents.get_by_role('button',name='Channels',exact=True)
            for _ in range(120):
                if await button.is_enabled():break
                await page.wait_for_timeout(250)
            await button.click();surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page)
            row=surface.get_by_role('listitem').filter(has_text=CHANNEL_NAME).filter(has_text='/'+SLUG);await row.wait_for(state='visible',timeout=30_000);await row.get_by_text('Public and available',exact=True).wait_for();await _capture(page,directory,'01-public-channel-available',shots)
            public_status['before']=(await page.request.post(args.url+f'/api/public/agents/{SLUG}/sessions',data={})).status
            await row.get_by_role('button',name='Review pause',exact=True).click();review=page.locator('section.deployment-review');await review.get_by_role('heading',name='Approve hosted Web availability change',exact=True).wait_for(timeout=30_000);await _capture(page,directory,'02-pause-review',shots);await review.get_by_role('button',name='Keep current availability',exact=True).click();await review.wait_for(state='detached',timeout=30_000);await row.get_by_text('Public and available',exact=True).wait_for()
            await row.get_by_role('button',name='Review pause',exact=True).click();review=page.locator('section.deployment-review');await review.get_by_role('button',name='Apply availability change',exact=True).click();await review.wait_for(state='detached',timeout=30_000);await row.get_by_text('Public access paused',exact=True).wait_for(timeout=30_000);await _capture(page,directory,'03-public-access-paused',shots)
            public_status['paused']=(await page.request.post(args.url+f'/api/public/agents/{SLUG}/sessions',data={})).status
            await row.get_by_role('button',name='Review resume',exact=True).click();review=page.locator('section.deployment-review');await review.get_by_role('button',name='Apply availability change',exact=True).click();await review.wait_for(state='detached',timeout=30_000);await row.get_by_text('Public and available',exact=True).wait_for(timeout=30_000);await page.reload(wait_until='domcontentloaded');surface=page.locator('section.channels-home');await surface.get_by_role('heading',name='Channels and Deployment',exact=True).wait_for(timeout=60_000);await _maximize(page);row=surface.get_by_role('listitem').filter(has_text=CHANNEL_NAME).filter(has_text='/'+SLUG);await row.get_by_text('Public and available',exact=True).wait_for(timeout=30_000);await _capture(page,directory,'04-resumed-after-reload',shots)
            public_status['after']=(await page.request.post(args.url+f'/api/public/agents/{SLUG}/sessions',data={})).status
            if tasks:await asyncio.gather(*tuple(tasks),return_exceptions=True)
            after=_state();exact=[x['operationId'] for x in operations];required=['channels.set_enabled']*3;cursor=0
            for op in exact:
                if cursor<len(required) and op==required[cursor]:cursor+=1
            if cursor!=3:raise RuntimeError('The exact reviewed availability sequence was not observed.')
            if after!=before:raise RuntimeError('Channel/deployment identity was not restored after availability lifecycle.')
            if public_status!={'before':200,'paused':503,'after':200}:raise RuntimeError('Public session availability did not track the reviewed channel state.')
            unexpected_console=[x for x in diagnostics['consoleErrors'] if '409' not in x['text'] and '404' not in x['text']]
            if diagnostics['httpErrors'] or diagnostics['pageErrors'] or unexpected_console:raise RuntimeError('The Channel interval contains unexpected diagnostics.')
    except Exception as caught:error=f'{type(caught).__name__}: {caught}'
    finally:
        if page is not None and error is not None:
            try:await page.screenshot(path=directory/'99-failure.png',full_page=False)
            except Exception:pass
        if page is not None:
            try:
                raw=page.video
                if raw is not None:await page.close();video_path=Path(await raw.path())
            except Exception:pass
        if context is not None:
            try:await context.close()
            except Exception:pass
        if browser is not None:
            try:await browser.close()
            except Exception:pass
        if recovered:
            try:_owner_reset(destroy)
            except Exception as e:error=error or f'RuntimeError: temporary owner credential cleanup failed: {e}'
    if video_path is not None and video_path.is_file():final=directory/'phase5-channel-availability-normal-speed.webm';video_path.replace(final);video_path=final
    result={'runId':run_id,'status':'passed' if error is None else 'failed','scope':'isolated Phase 5 hosted Web availability lifecycle','ids':{'organizationId':ORGANIZATION_ID,'agentId':AGENT_ID,'channelId':CHANNEL_ID,'deploymentId':DEPLOYMENT_ID},'before':before,'after':after,'publicStatus':public_status,'operations':operations,'screenshots':shots,'video':None if video_path is None else str(video_path.relative_to(ROOT)),'videoMetadata':{'playbackRate':1.0,'width':1440,'height':1000,'maximizedSurface':True},'diagnostics':diagnostics,'elapsedSeconds':round(time.monotonic()-started,3),'error':error};path=directory/'result.json';path.write_text(json.dumps(result,indent=2)+'\n')
    for f in directory.rglob('*'):
        if f.is_file() and (password.encode() in f.read_bytes() or destroy.encode() in f.read_bytes()):shutil.rmtree(directory);raise RuntimeError('Credential canary reached Channel evidence; evidence removed.')
    print(f'run={run_id} status={result["status"]}');print(f'artifact={path}');print(f'video={result["video"]}');
    if error:print('error='+error.encode('ascii','backslashreplace').decode('ascii'))
    return 0 if error is None else 1

async def main():
    async with asyncio.timeout(13*60):return await run(arguments())
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
