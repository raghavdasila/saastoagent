from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Response, async_playwright

from run_phase5_builder_lifecycle_journey import RESET_CODE, _capture, _maximize, _submit_sign_in


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "phase5-evaluation-management"
CONTAINER = "corpus-development-backend-1"
OWNER_EMAIL = "horizontal-0ce5a301e6b6436b9faa323fb19f0978@example.com"
ORGANIZATION_ID = "93a96dba-5840-4c6e-9880-1e62aaea7f6c"
AGENT_ID = "3898dfc7-d177-489a-9537-06f0eaccf717"
AGENT_NAME = "Store Taxonomy Assistant"
BUILD_ID = "207b52c0-c02e-47df-9650-9d503fee0d7f"
FAILED_CASE_ID = "b327f5de-38a6-42ac-9c7b-722f0f18d7ad"
FAILED_ATTEMPT_ID = "2407a0fb-3f08-4b97-ab3c-eda164e029fd"
CRUD_CASE_ID = "3096a341-d746-4a48-b371-fee6035ffd07"
CRUD_TITLE = "Successful Sandbox interaction"


def arguments() -> argparse.Namespace:
    parser=argparse.ArgumentParser(description="Record isolated Evaluation CRUD and explicit run retry.")
    parser.add_argument("--url",default="http://127.0.0.1:5199"); parser.add_argument("--headed",action="store_true")
    return parser.parse_args()


def _owner_reset(password: str) -> dict[str,str]:
    done=subprocess.run(["docker","exec","-i","-w","/workspace/corpus/backend",CONTAINER,"python","-c",RESET_CODE,OWNER_EMAIL,AGENT_ID,ORGANIZATION_ID],input=password,text=True,capture_output=True,timeout=60,check=False)
    if done.returncode!=0: raise RuntimeError("The exact Evaluation owner could not be recovered.")
    return json.loads(done.stdout.strip())


def _state() -> dict[str,object]:
    code=r"""
import json,sqlite3,sys
org,agent,build,failed_case,crud_case=sys.argv[1:]
db=sqlite3.connect('/var/lib/corpus/corpus.sqlite3');db.row_factory=sqlite3.Row
cases=db.execute('''select id,build_id,title,category,difficulty,current_revision,removed_at from agent_evaluation_cases where replace(lower(organization_id),'-','')=replace(lower(?),'-','') and replace(lower(id),'-','') in (replace(lower(?),'-',''),replace(lower(?),'-','')) order by id''',(org,failed_case,crud_case)).fetchall()
attempts=db.execute('''select id,case_id,build_id,case_revision,retry_of_attempt_id,status,failure_code from agent_evaluation_run_attempts where replace(lower(organization_id),'-','')=replace(lower(?),'-','') and replace(lower(case_id),'-','')=replace(lower(?),'-','') order by created_at''',(org,failed_case)).fetchall()
revisions=db.execute('''select id,case_id,revision,title,category,difficulty from agent_evaluation_case_revisions where replace(lower(organization_id),'-','')=replace(lower(?),'-','') and replace(lower(case_id),'-','')=replace(lower(?),'-','') order by revision''',(org,crud_case)).fetchall()
print(json.dumps({'cases':[dict(x) for x in cases],'attempts':[dict(x) for x in attempts],'revisions':[dict(x) for x in revisions]}));db.close()
"""
    done=subprocess.run(["docker","exec","-w","/workspace/corpus/backend",CONTAINER,"python","-c",code,ORGANIZATION_ID,AGENT_ID,BUILD_ID,FAILED_CASE_ID,CRUD_CASE_ID],text=True,capture_output=True,timeout=30,check=False)
    if done.returncode!=0: raise RuntimeError("The exact Evaluation state is unavailable.")
    return json.loads(done.stdout)


async def run(args: argparse.Namespace) -> int:
    run_id=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")+"-"+secrets.token_hex(4); directory=ARTIFACT_ROOT/run_id; videos=directory/"raw-video"; videos.mkdir(parents=True)
    screenshots=[];operations=[];diagnostics={"httpErrors":[],"consoleErrors":[],"pageErrors":[],"requestFailures":[]}
    password="Corpus-Evaluation-"+secrets.token_urlsafe(24)+"!9";destroy="Corpus-Evaluation-Destroy-"+secrets.token_urlsafe(24)+"!9"
    before=_state();after=None;browser=context=page=None;video_path=None;error=None;recovered=False;tasks=set();started=time.monotonic()
    async def observe(response:Response)->None:
        path=urlsplit(response.url).path
        expected_reject=path.startswith('/api/routedeck/reviews/') and path.endswith('/reject') and response.status==409
        if response.status>=400 and not expected_reject:
            failure={'method':response.request.method,'path':path,'status':response.status}
            if path=='/api/routedeck/dispatch':
                try:
                    body=await response.json()
                    failure['failureCode']=body.get('failure_code') or body.get('failureCode')
                    failure['detail']=body.get('detail') if isinstance(body.get('detail'),str) else None
                except Exception:pass
            diagnostics['httpErrors'].append(failure)
        if response.status==200 and response.request.method=='POST' and path=='/api/routedeck/dispatch':
            try:
                body=await response.json();op=body.get('operation_id') or body.get('operationId')
                if isinstance(op,str):operations.append({'operationId':op,'disposition':body.get('disposition'),'outcome':body.get('outcome')})
            except Exception:pass
    def schedule(response:Response)->None:
        task=asyncio.create_task(observe(response));tasks.add(task);task.add_done_callback(tasks.discard)
    try:
        if len(before['attempts']) not in {1,2} or before['attempts'][0]['status']!='failed' or before['attempts'][0]['id'].replace('-','')!=FAILED_ATTEMPT_ID.replace('-',''):raise RuntimeError('The retained failed Evaluation attempt preflight changed.')
        retry_already_recorded=len(before['attempts'])==2
        if retry_already_recorded and (before['attempts'][1]['retry_of_attempt_id'] or '').replace('-','')!=FAILED_ATTEMPT_ID.replace('-',''):raise RuntimeError('The retained Evaluation retry lineage changed.')
        crud=next((x for x in before['cases'] if x['id'].replace('-','')==CRUD_CASE_ID.replace('-','')),None)
        if crud is None or crud['removed_at'] is not None:raise RuntimeError('The disposable Evaluation case preflight changed.')
        identity=_owner_reset(password);recovered=True
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=not args.headed);context=await browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=videos,record_video_size={'width':1440,'height':1000});page=await context.new_page();page.on('response',schedule)
            page.on('console',lambda i:diagnostics['consoleErrors'].append({'type':i.type,'text':i.text}) if i.type in {'warning','error'} else None);page.on('pageerror',lambda i:diagnostics['pageErrors'].append({'message':str(i)}));page.on('requestfailed',lambda r:diagnostics['requestFailures'].append({'method':r.method,'path':urlsplit(r.url).path,'failure':r.failure}))
            await page.goto(args.url);await page.get_by_role('heading',name='Explore Corpus',exact=True).wait_for(timeout=30_000);await page.get_by_role('button',name='Sign in',exact=True).click();await page.get_by_role('heading',name='Sign in',exact=True).wait_for();await _submit_sign_in(page,identity['email'],password);await page.get_by_label('Sign out',exact=True).wait_for(timeout=30_000)
            await page.locator('section.workspace-home').get_by_role('button',name='Open Agents',exact=True).click();agents=page.locator('section.agents-home');await agents.locator('#agents-home-title').wait_for(timeout=30_000);agent=agents.get_by_label('Agent inventory').get_by_role('button').filter(has_text=AGENT_NAME);await agent.wait_for(state='visible',timeout=30_000)
            if await agent.count()!=1:raise RuntimeError('The exact Evaluation Agent is unavailable or ambiguous.')
            await agent.click();button=agents.get_by_role('button',name='Evaluation',exact=True)
            for _ in range(120):
                if await button.is_enabled():break
                await page.wait_for_timeout(250)
            await button.click();surface=page.locator('section.evaluation-home');await surface.get_by_role('heading',name='Evaluation',exact=True).wait_for(timeout=60_000);await _maximize(page)
            build_select=surface.get_by_label('Exact build',exact=True);await build_select.wait_for(state='visible',timeout=30_000);await build_select.select_option(BUILD_ID);await page.wait_for_timeout(1_000)
            failed_row=surface.get_by_role('row').filter(has_text=FAILED_CASE_ID[:0] or 'I need to see a list of product tags')
            await failed_row.wait_for(state='visible',timeout=30_000);await failed_row.scroll_into_view_if_needed();await _capture(page,directory,'01-failed-run',screenshots)
            if not retry_already_recorded:
                async with page.expect_response(lambda r:urlsplit(r.url).path=='/api/routedeck/dispatch' and r.request.method=='POST') as retry_response_info:
                    await failed_row.get_by_role('button',name='Retry failed run',exact=True).click()
                retry_response=await retry_response_info.value
                if retry_response.status!=200:
                    try: retry_failure=await retry_response.json()
                    except Exception: retry_failure={}
                    safe_retry_failure={key:value for key,value in retry_failure.items() if key not in {'arguments','headers','cookies','request_body','response_body'} and isinstance(value,(str,int,float,bool,type(None)))}
                    raise RuntimeError('Evaluation retry dispatch failed: '+json.dumps(safe_retry_failure,sort_keys=True))
                for _ in range(180):
                    text=await failed_row.inner_text()
                    if 'Queued' not in text and 'Running' not in text:break
                    await page.wait_for_timeout(500)
            await _capture(page,directory,'02-explicit-retry-recorded',screenshots)
            crud_row=surface.get_by_role('row').filter(has_text=CRUD_TITLE);await crud_row.wait_for(state='visible',timeout=30_000);await crud_row.get_by_role('button',name='Edit',exact=True).click()
            title_input=surface.get_by_label('Edit case title',exact=True);await title_input.wait_for(state='visible',timeout=30_000)
            await title_input.fill('Phase 5 retained Sandbox case');await surface.get_by_label('Edit case category',exact=True).fill('lifecycle-recovery');await surface.get_by_label('Edit case difficulty',exact=True).select_option('medium');await surface.get_by_role('button',name='Save revision',exact=True).click();crud_row=surface.get_by_role('row').filter(has_text='Phase 5 retained Sandbox case');await crud_row.wait_for(state='visible',timeout=30_000)
            await crud_row.get_by_role('button',name='Remove',exact=True).click();review=page.locator('section.evaluation-delete-review');await review.get_by_role('heading',name='Remove this evaluation case?',exact=True).wait_for(timeout=30_000);await _capture(page,directory,'03-removal-review',screenshots);await review.get_by_role('button',name='Keep case',exact=True).click();await review.wait_for(state='detached',timeout=30_000)
            crud_row=surface.get_by_role('row').filter(has_text='Phase 5 retained Sandbox case');await crud_row.get_by_role('button',name='Remove',exact=True).click();review=page.locator('section.evaluation-delete-review');await review.get_by_role('button',name='Remove case',exact=True).click();await review.wait_for(state='detached',timeout=30_000)
            await page.reload(wait_until='domcontentloaded');surface=page.locator('section.evaluation-home');await surface.get_by_role('heading',name='Evaluation',exact=True).wait_for(timeout=60_000);await _maximize(page);build_select=surface.get_by_label('Exact build',exact=True);await build_select.wait_for(state='visible',timeout=30_000);await build_select.select_option(BUILD_ID);removed=surface.get_by_role('row').filter(has_text='Phase 5 retained Sandbox case');await removed.get_by_text('Removed from future evaluation',exact=True).wait_for(timeout=30_000);await _capture(page,directory,'04-reload-removed-history',screenshots)
            if tasks:await asyncio.gather(*tuple(tasks),return_exceptions=True)
            after=_state();attempts=after['attempts']
            if len(attempts)!=2 or attempts[1]['retry_of_attempt_id'].replace('-','')!=FAILED_ATTEMPT_ID.replace('-',''):raise RuntimeError('Explicit Evaluation retry did not append exact lineage.')
            crud=next(x for x in after['cases'] if x['id'].replace('-','')==CRUD_CASE_ID.replace('-',''))
            if crud['current_revision']!=2 or crud['removed_at'] is None:raise RuntimeError('Evaluation edit/removal did not persist exact revision history.')
            if len(after['revisions'])!=2:raise RuntimeError('Evaluation case revision lineage changed unexpectedly.')
            required=([] if retry_already_recorded else ['evaluation.retry_case_run'])+['evaluation.edit_case','evaluation.delete_case','evaluation.delete_case'];cursor=0
            for op in [x.get('operationId') for x in operations]:
                if cursor<len(required) and op==required[cursor]:cursor+=1
            if cursor!=len(required):raise RuntimeError('The exact supervised Evaluation sequence was not observed.')
            if diagnostics['httpErrors'] or diagnostics['pageErrors']:raise RuntimeError('The Evaluation interval contains unexpected diagnostics.')
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
    if video_path is not None and video_path.is_file():final=directory/'phase5-evaluation-management-normal-speed.webm';video_path.replace(final);video_path=final
    result={'runId':run_id,'status':'passed' if error is None else 'failed','scope':'isolated Phase 5 Evaluation CRUD and explicit run retry','ids':{'organizationId':ORGANIZATION_ID,'agentId':AGENT_ID,'buildId':BUILD_ID,'failedCaseId':FAILED_CASE_ID,'failedAttemptId':FAILED_ATTEMPT_ID,'crudCaseId':CRUD_CASE_ID},'before':before,'after':after,'operations':operations,'screenshots':screenshots,'video':None if video_path is None else str(video_path.relative_to(ROOT)),'videoMetadata':{'playbackRate':1.0,'width':1440,'height':1000,'maximizedSurface':True},'diagnostics':diagnostics,'elapsedSeconds':round(time.monotonic()-started,3),'error':error}
    result_path=directory/'result.json';result_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for f in directory.rglob('*'):
        if f.is_file() and (password.encode() in f.read_bytes() or destroy.encode() in f.read_bytes()):shutil.rmtree(directory);raise RuntimeError('Credential canary reached the Evaluation evidence directory; evidence removed.')
    print(f"run={run_id} status={result['status']}");print(f'artifact={result_path}');print(f"video={result['video']}")
    if error:print('error='+error.encode('ascii','backslashreplace').decode('ascii'))
    return 0 if error is None else 1


async def main()->int:
    async with asyncio.timeout(13*60):return await run(arguments())


if __name__=='__main__':raise SystemExit(asyncio.run(main()))
