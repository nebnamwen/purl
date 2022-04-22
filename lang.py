class _base_verb(object):
    def _do(self, ndl):
        raise NotImplementedError

    def __mul__(self, n):
        return [self] * n

class _adverb(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value

front = _adverb('front_or_back', 1)
back = _adverb('front_or_back', -1)
through_back_of_loop = _adverb('through_back_of_loop', True)
from_cable_needle = _adverb('from_cable_needle', True)

class _with_color(_base_verb):
    def __init__(self, c, items):
        self.color = c
        self.items = items

    def _do(self, ndl):
        old_color = ndl.color
        ndl.color = self.color

        result = ndl.do(*self.items)

        ndl.color = old_color

        return result

class color(_adverb):
    def __init__(self, raw_color):
        _adverb.__init__(self, 'color', raw_color)

    def __call__(self, *args):
        return _with_color(self.value, args)

    def _do(self, ndl):
        ndl.color = self.color

class turn(_base_verb):
    def _do(self, ndl):
        ndl.turn()
        return []
turn = turn()

class _verb_with_params(_base_verb):
    _adverbs_allowed = []
    _init_adverb_dict = {}

    def __init__(self, *args):
        self._adverb_dict = self._init_adverb_dict.copy()
        self._parameter = None
        for item in args:
            if hasattr(item, 'key'):
                self._apply_adverb(item)
            else:
                self._apply_parameter(item)

    def _apply_adverb(self, item):
        key, value = item.key, item.value
        # FIX ERROR HANDLING
        if key not in self._adverbs_allowed or key in self._adverb_dict:
            raise ValueError
        else:
            self._adverb_dict[key] = value

    def _apply_parameter(self, item):
        # FIX ERROR HANDLING
        if self._parameter is not None:
            raise ValueError
        else:
            self._parameter = item

class _repeating_verb(_verb_with_params):

    def _do(self, ndl):
        result = []
        for i in range(1 if self._parameter is None else self._parameter):
            result.extend(self._do_once(ndl))
        return result

    def _do_once(self, ndl):
        raise NotImplementedError

class _clonable_verb(_verb_with_params):

    def _get_clone_args(self):
        return (
            [self._parameter] +
            [ _adverb(key, self._adverb_dict[key]) for key in self._adverb_dict
              if key not in self._init_adverb_dict ])

    def __call__(self, *args):
        return type(self)(*(self._get_clone_args() + list(args)))

_work_stitch_adverbs_allowed = [ 'knit_or_purl', 'through_back_of_loop', 'from_cable_needle', 'color' ]

class _work_one_stitch(_repeating_verb, _clonable_verb):
    _adverbs_allowed = _work_stitch_adverbs_allowed

    def _do_once(self, ndl):
        return ndl.create_node(1, 1, **self._adverb_dict)

class knit(_work_one_stitch):
    _init_adverb_dict = { 'knit_or_purl': 1 }
knit = knit()

class purl(_work_one_stitch):
    _init_adverb_dict = { 'knit_or_purl': -1 }
purl = purl()

class _work_stitches_together(_clonable_verb):
    _adverbs_allowed = _work_stitch_adverbs_allowed

    def _do(self, ndl):
        return ndl.create_node(self._parameter, 1, **self._adverb_dict)

class knit_together(_work_stitches_together):
    _init_adverb_dict = { 'knit_or_purl': 1 }

class purl_together(_work_stitches_together):
    _init_adverb_dict = { 'knit_or_purl': -1 }

class yarnover(_base_verb):
    def _do(self, ndl):
        return ndl.yarnover()
yarnover = yarnover()

class slip(_repeating_verb, _clonable_verb):
    _adverbs_allowed = [ 'front_or_back' ]

    def _do_once(self, ndl):
        return ndl.slip_stitch(**self._adverb_dict)

class slip_to_cable_needle(_verb_with_params):
    _adverbs_allowed = [ 'front_or_back' ]

    def _do(self, ndl):
        return ndl.slip_to_cable_needle(self._parameter, **self._adverb_dict)

class into_same_stitch(_base_verb):

    def __init__(self, first, *rest):
        self._validate_first(first)
        for item in rest:
            self._validate_rest(item)

        self.first = first
        self.rest = [ _work_into_same_stitch(item) for item in rest ]

    def _validate_first(self, item):
        ## FIX
        pass

    def _validate_rest(self, item):
        ## FIX
        pass

    def _do(self, ndl):
        result = []
        for item in [self.first] + self.rest:
            result.extend(ndl.do(item))
        return result

class _work_into_same_stitch(_base_verb):
    _adverbs_allowed = [ 'knit_or_purl', 'through_back_of_loop', 'color' ]

    def __init__(self, verb):
        self._validate_verb(verb)
        self._adverb_dict = verb._adverb_dict.copy()

    def _validate_verb(self, verb):
        ## FIX
        pass

    def _do(self, ndl):
        return ndl.work_into_current_node(**self._adverb_dict)

knit_front_and_back = into_same_stitch(knit(1), knit(1, through_back_of_loop))
purl_front_and_back = into_same_stitch(purl(1), purl(1, through_back_of_loop))

class if_right_side(_base_verb):
    ## REVIEW INTERFACE
    ## ? if_right_side([A1,A2],[B1,B2])
    ## ? if_right_side(A1,A2)(B1,B2)
    ## ? if_right_side(A1,A2).otherwise(B1,B2) ## can't be 'else' because it's reserved
    def __init__(self, right_side, wrong_side):
        self.right_side = right_side
        self.wrong_side = wrong_side

    def _do(self, ndl):
        if ndl.orientation == 1:
            return ndl.do(self.right_side)
        else:
            return ndl.do(self.wrong_side)
