import unittest

import source

class TestSource(unittest.TestCase):

    def setUp(self):
        self.pano_path = "http://host/pano-path"

    def test_sources(self):
        keys = ['cube', 'sphere']
        pano_sources = source.sources(self.pano_path, keys)
        print pano_sources

if __name__ == '__main__':
    unittest.main()