import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest.mock import Mock

BASE = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dashboard_generator',BASE/'tools/generar_dashboard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
spec2 = importlib.util.spec_from_file_location('image_inspector',BASE/'tools/inspeccionar_imagen.py')
inspector = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(inspector)


class DashboardTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(module.run_category({'path':'.github/workflows/ai-devops.yml@refs/heads/main'}),'ai')
        self.assertEqual(module.run_category({'path':'.github/workflows/demo-imagen-ghcr.yml@refs/heads/main'}),'cd')
        self.assertEqual(module.run_category({'path':'.github/workflows/codeql.yml@refs/heads/main'}),'security')
        self.assertEqual(module.run_category({'path':'.github/workflows/ci.yml@refs/heads/main'}),'ci')

    def test_summary(self):
        runs=[{'conclusion':'success','category':'ci'}, {'conclusion':'failure','category':'ai'}, {'conclusion':'pending','category':'cd'}]
        self.assertEqual(module.summarize(runs)['failure'],1)
        self.assertEqual(module.summarize(runs)['other'],1)
        self.assertEqual(module.summarize(runs)['latest']['ci']['category'],'ci')

    def test_snapshot_handles_api_failure_without_fake_success(self):
        def fail(repo,path,token):return None,'GitHub API HTTP 403'
        def unavailable(repo):return module.inspect_image_placeholder(repo),['Docker no disponible']
        data=module.build_snapshot('Ryob1239/metadata-action-IA',fetcher=fail,inspector=unavailable)
        self.assertEqual(data['status'],'partial')
        self.assertEqual(data['stats']['total'],0)
        self.assertFalse(data['image']['available'])
        self.assertTrue(data['warnings'])

    def test_snapshot_counts_real_run(self):
        raw={'path':'.github/workflows/ci.yml@refs/heads/main','name':'ci','id':5,'status':'completed','conclusion':'success','html_url':'https://github.com/a/b/actions/runs/5'}
        def fetch(repo,path,token):return ({'workflow_runs':[raw]} if path.startswith('actions') else {'description':'Ejemplo','private':False}),None
        data=module.build_snapshot('a/b',fetcher=fetch,inspector=lambda repo:(module.inspect_image_placeholder(repo),[]))
        self.assertEqual(data['status'],'synced')
        self.assertEqual(data['stats']['success'],1)
        self.assertEqual(data['runs'][0]['category'],'ci')

    def test_invalid_repo_is_rejected(self):
        with self.assertRaises(ValueError):module.build_snapshot('owner/../bad')

    def test_untrusted_url_dropped(self):
        a=[{'html_url':'javascript:alert(1)','conclusion':'success'}, {'html_url':'https://github.com/a/b/actions/runs/2','conclusion':'success'}]
        self.assertEqual(len(module.normalize_runs(a)),1)

    def test_site_generates_static_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            module.write_site({'schema_version':1,'runs':[]},pathlib.Path(tmp))
            self.assertTrue((pathlib.Path(tmp)/'index.html').exists())
            self.assertTrue((pathlib.Path(tmp)/'styles.css').exists())
            self.assertEqual(json.loads((pathlib.Path(tmp)/'data/dashboard.json').read_text())['schema_version'],1)

    def test_tag_validation(self):
        self.assertTrue(inspector.TAG_RE.fullmatch('sha-64ed0b2'))
        self.assertFalse(inspector.TAG_RE.fullmatch('latest; rm -rf /'))
        self.assertFalse(inspector.TAG_RE.fullmatch('evil/latest'))

    def test_inspector_runs_docker_and_validates_output(self):
        import subprocess
        recorded=[]
        def fake_runner(args,**kwargs):
            recorded.append(args)
            if args[1]=='pull': output='done'
            elif args[1]=='image':
                output=json.dumps({'Config':{'Labels':{'org.opencontainers.image.title':'Metadata Action IA'}},'Architecture':'amd64','Os':'linux','RepoDigests':['x@sha256:123'],'Size':100})
            elif args[1]=='run' and '--entrypoint' not in args:output='{"ejecutado":true,"proyecto":"Metadata Action IA"}'
            else:output='demo.mjs\n'
            return subprocess.CompletedProcess(args,0,stdout=output,stderr='')
        data=inspector.execute('ghcr.io/a/b:latest',runner=fake_runner)
        self.assertTrue(data['program']['ejecutado'])
        self.assertEqual(data['architecture'],'amd64')
        self.assertEqual(len(recorded),4)

    def test_report_contains_real_result(self):
        report=inspector.report_md({'date_utc':'2026-11-25T00:00:00Z','image':'ghcr.io/a/b:latest','program':{'ejecutado':True},'os':'linux','architecture':'amd64','digests':['sha256:123'],'labels':{},'files_output':'demo.mjs'})
        self.assertIn('ejecutado',report)
        self.assertIn('sha256:123',report)


if __name__=='__main__':unittest.main()
