from collections.abc import Mapping, Iterable

class chart(object):

    def __init__(self, *args):
        rows = []
        if len(args) == 1:
            rows = args[0]
        elif len(args) == 2:
            key = args[0]
            rowstr = args[1]
            rows = self._rows_from_key_and_str(key,rowstr)
        else:
            raise TypeError

        self.rows = rows

    @staticmethod
    def _rows_from_key_and_str(key, rowstr):
        if not isinstance(key, Mapping) or not isinstance(rowstr, str):
            raise TypeError

        # coerce newlines
        if "\n" in rowstr:
            rowstr = rowstr.replace("\r", "")
        else:
            rowstr = rowstr.replace("\r", "\n")

        rows = [ [ key[i] for i in reversed(r.strip().split()) ] for r in reversed(rowstr.split("\n")) if len(r.strip()) > 0 ]

        return rows

    def _do(self, needle):
        result = []
        for row in self.rows:
            oriented_row = row if needle.orientation == 1 else reversed(row)
            result.extend(needle.do(oriented_row))
            needle.end_row()
        return result

    def __add__(self, other):
        if len(self.rows) != len(other.rows):
            raise ValueError
        return chart([ other.rows[i] + self.rows[i] for i in range(len(self.rows)) ])

    def __truediv__(self, other):
        return chart(other.rows + self.rows)

    def __mul__(self, n):
        return chart([ row * n for row in self.rows ])

    def __pow__(self, n):
        return chart(self.rows * n)
