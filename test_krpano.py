import os
import unittest

import krpano


class TestKrpano(unittest.TestCase):

    def setUp(self):
        self.image_path = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "pano_8192.jpg"))

    def test_title(self):
        krpano.tile_full(self.image_path)


if __name__ == '__main__':
    unittest.main()