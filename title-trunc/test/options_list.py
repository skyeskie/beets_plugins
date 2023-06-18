#  Copyright (c) 2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt

import unittest

from beetsplug.title_trunc.command import select_from_options


class MyTestCase(unittest.TestCase):
    def test_basic(self):
        sel = select_from_options(
            'This is the end of the world as we know it',
            'End of the World', 20
        )
        self.assertEqual([
            'This is the end of …',
            'This is th…we know it',
            'End of the World'
        ], sel)  # add assertion here

    def test_colons(self):
        sel = select_from_options(
            'This is: the end of: the world (as we know it)',
            None, 20
        )
        self.assertEqual([
            'This is: the end of…',
            'This is: t…e know it)'
        ], sel)


if __name__ == '__main__':
    unittest.main()
