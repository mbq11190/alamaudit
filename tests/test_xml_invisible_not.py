import os
import unittest


class TestXmlInvisibleNot(unittest.TestCase):
    def test_no_invisible_not_patterns(self):
        root = os.path.dirname(os.path.dirname(__file__))
        bad_files = []
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith('.xml'):
                    continue
                path = os.path.join(dirpath, fn)
                text = open(path, 'r', encoding='utf-8').read()
                if 'invisible="not ' in text:
                    bad_files.append(path)
        self.assertEqual(bad_files, [], f"Files still contain 'invisible=\"not ...\"' patterns: {bad_files}")
