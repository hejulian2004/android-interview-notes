import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import read_data, collect_files
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
    def test_deterministic_generation(self):
        self.assertEqual(collect_files(),collect_files())
    def test_dry_run_has_no_commands(self):
        with patch.object(publish,'run',side_effect=AssertionError('no process allowed')):
            self.assertEqual(publish.main(['--dry-run']),0)
    def test_private_is_default(self):
        self.assertFalse(publish.parse_args([]).public)
    def test_malformed_repo_rejected(self):
        with self.assertRaises(SystemExit): publish.parse_args(['--repo','https://github.com/o/r'])
if __name__=='__main__': unittest.main()
