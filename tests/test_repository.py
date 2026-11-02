import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import read_data, collect_files, question_path
from validate import validate_data, check_links
import publish

class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.sources,cls.questions,cls.refs=read_data()
    def test_real_data_valid(self):
        self.assertEqual(validate_data(self.sources,self.questions,self.refs),[])
    def test_pending_source_rejected(self):
        qs=copy.deepcopy(self.questions);qs[0]['evidence'][0]['source_id']='S018'
        self.assertTrue(any('待核来源' in e for e in validate_data(self.sources,qs,self.refs)))
    def test_missing_evidence_rejected(self):
        qs=copy.deepcopy(self.questions);qs[0]['evidence']=[]
        self.assertTrue(any('缺少来源' in e for e in validate_data(self.sources,qs,self.refs)))
    def test_supplement_attribution_rejected(self):
        qs=copy.deepcopy(self.questions);q=next(q for q in qs if q['kind']=='supplement')
        q['evidence']=[dict(source_id='S001',observed_variant='fake')]
        self.assertTrue(any('补充题不得' in e for e in validate_data(self.sources,qs,self.refs)))
    def test_links(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'README.md').write_text('[bad](missing.md)',encoding='utf8')
            self.assertEqual(len(check_links(p)),1)
            (p/'missing.md').write_text('ok',encoding='utf8')
            self.assertEqual(check_links(p),[])
    def test_link_check_excludes_only_web_generated_docs_and_named_fixtures(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            ignored=[
                'web/node_modules/example/README.md',
                'web/dist/README.md',
                'web/tests/fixture-markdown-edge.md',
                'web/tests/fixture-emphasis-real.md',
            ]
            authored=[
                'docs/guide.md',
                'docs/fixture-markdown-edge.md',
                'docs/dist/README.md',
                'web/README.md',
                'web/tests/README.md',
            ]
            for name in ignored+authored:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text('[broken](missing.md)',encoding='utf8')
            errors=check_links(root)
            self.assertEqual(len(errors),len(authored))
            for name in authored:
                self.assertTrue(any(e.startswith(name+': 本地链接不存在 ') for e in errors),name)
            for name in ignored:
                self.assertFalse(any(e.startswith(name+': ') for e in errors),name)

    def test_generated_readme_keeps_mobile_entry_and_editorial_guides(self):
        generated,_=collect_files()
        readme=generated['README.md']
        for name in ('java-core','kotlin-coroutines','android-platform'):
            self.assertIn('(docs/'+name+'-interview-guide.md)',readme)
        self.assertIn('120 题为整理者设计的通用练习',readme)
        self.assertIn('不进入来源题、公司或招聘频率统计',readme)
        self.assertIn('(https://txy.hejulian.org/android-study/)',readme)
        self.assertIn('(web/README.md)',readme)
        self.assertNotIn('371 道题',readme)
        self.assertNotIn('7 篇完整导读',readme)

    def test_deterministic_generation(self):
        self.assertEqual(collect_files(),collect_files())

    def test_persisted_question_path_survives_title_edit(self):
        q=copy.deepcopy(self.questions[0]); original=question_path(q)
        q['source_path']=original;q['title']='编辑后的标题'
        self.assertEqual(question_path(q),original)

    def test_persisted_question_path_rejects_out_of_scope_files(self):
        q=copy.deepcopy(self.questions[0])
        for path in ('../README.md','questions/../README.md','web/src/app.mjs',
                     'supplements/category/'+q['id']+'-title.md',
                     'questions/category/Q999-title.md'):
            q['source_path']=path
            with self.assertRaises(ValueError): question_path(q)
    def test_dry_run_has_no_commands(self):
        with patch.object(publish,'run',side_effect=AssertionError('no process allowed')):
            self.assertEqual(publish.main(['--dry-run']),0)
    def test_private_is_default(self):
        self.assertFalse(publish.parse_args([]).public)
    def test_malformed_repo_rejected(self):
        with self.assertRaises(SystemExit): publish.parse_args(['--repo','https://github.com/o/r'])
if __name__=='__main__': unittest.main()
