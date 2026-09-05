"""Optional Playwright smoke: actual browser recomputation, both themes and widths.
Uses an already-installed Chromium; does not download browsers.
"""
import adapter as a
import audit
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--chromium',default='/usr/bin/chromium')
    p.add_argument('--out',type=Path,default=HERE/'browser-qa.json')
    args=p.parse_args()
    html=(ROOT/'site/evidence-time-machine.en.html').read_text(encoding='utf8')
    errors=[]; network=[]; checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1120},color_scheme='dark',reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:network.append(r.url) if r.url.startswith(('http://','https://')) else None)
        page.set_content(html,wait_until='load')
        page.wait_for_function('window.evidenceDemo && window.evidenceDemo.state')
        fixture_cases=[dict(id=cid,episode=e,expected=expected,baseline=audit.outcome(a.policy.reference_evaluate,e)) for cid,e,expected in audit.cases()]
        parity=page.evaluate('''(fixtureCases) => {
            const d=window.evidenceDemo;let checks=0;
            for(const c of fixtureCases){
              for(const [h,expected] of [[false,c.baseline],[true,c.expected]]){
                const got=d.evaluate(c.episode,c.episode.checkpoints[0],h).status;
                if(got!==expected)throw new Error(c.id+': '+got+' != '+expected);
                checks++;
              }
            }
            for(const q of d.data.results.real_queries){
              for(const h of [false,true]){
                const got=d.evaluate(d.data.real_episode,q.query,h).status;
                if(got!==q.expected)throw new Error(q.id+': '+got+' != '+q.expected);
                checks++;
              }
            }
            return checks;
        }''',fixture_cases)
        for theme in ('dark','light'):
            page.emulate_media(color_scheme=theme)
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':1120 if width==1440 else 844})
                for scenario in ('real','scope','defect'):
                    page.click('#s-'+scenario)
                    for pos in (0,1):
                        page.evaluate('(p)=>window.evidenceDemo.setPosition(p)',pos)
                        state=page.evaluate('window.evidenceDemo.state')
                        expected={('real',0):('UNKNOWN','UNKNOWN'),('real',1):('SUPPORTED','SUPPORTED'),
                          ('scope',0):('SUPPORTED','SUPPORTED'),('scope',1):('UNKNOWN','UNKNOWN'),
                          ('defect',0):('SUPPORTED','SUPPORTED'),('defect',1):('UNKNOWN','SUPPORTED')}[(scenario,pos)]
                        assert (state['baseline'],state['candidate'])==expected,state
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),(theme,width,scenario)
                        checks.append(dict(theme=theme,width=width,scenario=scenario,position=pos,pass_=True))
                if theme=='dark':
                    page.click('#s-defect')
                    page.screenshot(path=str(ROOT/f'demo-{width}.png'),full_page=(width==390))
        # Exercise the download path: this must produce actual JSON with matching data.
        with page.expect_download() as pending: page.click('#download')
        download=pending.value
        target=ROOT/'download-check.json';download.save_as(str(target))
        assert json.loads(target.read_text())['source_snapshot_sha256']==page.evaluate('window.evidenceDemo.data.results.source_snapshot_sha256')
        target.unlink()
        browser.close()
    assert not errors,errors
    assert not network,network
    result=dict(browser='Installed Chromium via Playwright; authored HTML rendered with set_content (file navigation unavailable in this environment)',python_javascript_verdict_checks=parity,
                view_state_checks=len(checks),themes=['dark','light'],widths=[1440,390],
                download_json_verified=True,horizontal_overflow=False,page_errors=errors,external_requests=network,
                checks=checks,boundary='Smoke coverage, not cross-browser or assistive-technology certification.')
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
