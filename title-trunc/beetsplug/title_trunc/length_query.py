#  Copyright (c) 2023
#  Author: Scott Yeskie
#  License: See LICENSE.txt

from beets.dbcore.query import NumericQuery


class MaxLengthQuery(NumericQuery):
    def __init__(self, field, pattern, fast=True):
        super().__init__(field, pattern, fast)
        self.maxlen = self._convert(pattern)

    def match(self, item):
        if self.field not in item:
            return False
        value = item[self.field]
        return len(value) <= self.maxlen

    def col_clause(self):
        return f'len({self.field}) <= ?', (self.maxlen,)
