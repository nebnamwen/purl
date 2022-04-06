import math
from numpy import array, ndarray, cross
from numpy.linalg import norm
from collections import deque
from collections.abc import Iterable

from model import mesh, node, yo_node, h_edge, v_edge, crossover, force

class __base(object):
    def __init__(self, rpi=5, spi=5, wpi=15, color="gray"):
        self.rpi = rpi
        self.spi = spi
        self.wpi = wpi
        self.color = color

        self.mesh = mesh()

        self.stitches = deque()
        self.loose_edge = None
        self.orientation = 1

        self.cable_stitches = deque()
        self.cable_side = None

        self._current_node = None
        self._to_be_relaxed = 0

    def _row_height(self): return 1.0 / self.rpi
    def _stitch_width(self): return 1.0 / self.spi
    def _yarn_thickness(self): return 1.0 / self.wpi

    def do(self, *args):
        for item in args:
            if isinstance(item, str):
                raise TypeError
            elif isinstance(item, Iterable):
                self.do(*item)
            else:
                item._do(self)

    def _displace(self, pos):
        raise NotImplementedError

    def cast_on(self, N):
        raise NotImplementedError

    def _arrow(self, pos):
        raise NotImplementedError

    def _relax(self):
        if not self.cable_stitches:
            self._relax_nodes(self._find_nodes_to_relax())
            self._to_be_relaxed = 0
            self.cable_side = None
        
    def _find_nodes_to_relax(self):
        working = []
        interval = 0

        working.append(self.stitches[-1].before if self.stitches[-1] else None)

        i = 0
        while interval < self._stitch_width() * 2 or len(working) < self._to_be_relaxed + 2:
            s = self.stitches[i]
            if s is None:
                working.append(s)
                interval = self._stitch_width() * 2
            elif s.before is working[-1]:
                pass
            else:
                s = s.before
                if working[-1] is not None:
                    interval += self._arrow(s.pos).dot(working[-1].pos - s.pos)
                working.append(s)

            i += 1

        return working

    def _relax_nodes(self, working):
        for k in range(len(working)*15):
            forces = []
            for i in range(1,len(working) - 1):
                for j in (-1,1):
                    if working[i+j] is not None:
                        arrow = self._arrow(working[i].pos)
                        target = working[i+j].pos + j*self._stitch_width()*arrow
                        delta = arrow * arrow.dot(target - working[i].pos)
                        delta *= 0.5
                        forces.append(force(working[i], delta))
            for f in forces: f.apply()

    def _pop_stitch(self, from_cable=False):
        q = self.cable_stitches if from_cable else self.stitches
        s = q.pop()
        if s is None:
            raise ValueError
        return s

    def _push_stitch(self, s, from_cable=False):
        self.stitches.appendleft(s)
        if self.cable_stitches and self.cable_side and not from_cable:
            for cs in self.cable_stitches:
                crossover(self.mesh, s, cs, self.cable_side * self.orientation, self._yarn_thickness())

    def create_node(self, pull, push, knit_or_purl=0, through_back_of_loop=False, from_cable_needle=False, color=None, node_class=None):
        inbound = []
        newpos = None

        if isinstance(pull, ndarray):
            newpos = pull
        elif isinstance(pull, int):
            if pull > 0:
                inbound = [self._pop_stitch(from_cable_needle) for i in range(pull)]
                newpos = self._displace(sum([s.before.pos for s in inbound]) / len(inbound))
            else:
                if self.loose_edge:
                    newpos = self.loose_edge.before.pos
                elif self.stitches and self.stitches[-1]:
                    newpos = self._displace(self.stitches[-1].before.pos)
                else:
                    raise ValueError
        else:
            raise TypeError

        color = color or self.color
        node_class = node_class or node

        new_node = node_class(self.mesh, newpos, self.orientation, knit_or_purl, self.loose_edge, inbound)

        for i in range(push):
            self._push_stitch(v_edge(self.mesh, new_node, self._row_height(), color, self._yarn_thickness()), from_cable_needle)

        self.loose_edge = h_edge(self.mesh, new_node, self._stitch_width(), color, self._yarn_thickness())

        self._current_node = new_node

        if isinstance(pull, int):
            self._to_be_relaxed += 1
            self._relax()

    def work_into_current_node(self, knit_or_purl=0, through_back_of_loop=False, color=None):
        if self._current_node is None:
            raise ValueError
        self._push_stitch(v_edge(self.mesh, self._current_node, self._row_height(), color or self.color, self._yarn_thickness()))

    def slip_to_cable_needle(self, N, front_or_back=0):
        if N > 0:
            for i in range(N):
                self.cable_stitches.appendleft(self._pop_stitch())
            self.cable_side = front_or_back

    def yarnover(self):
        self.create_node(0, 1, node_class=yo_node)
        self.stitches[0].length = self._yarn_thickness()

    def slip_stitch(self, front_or_back=0):
        s = self._pop_stitch()
        self._push_stitch(s)
        if self.loose_edge:
            self.loose_edge.length += self._stitch_width()
            if front_or_back:
                crossover(self.mesh, s, self.loose_edge, front_or_back * self.orientation, self._yarn_thickness())

    def turn(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None
        self.stitches.reverse()
        self.orientation *= -1

    def end_row(self):
        pass

    def cast_off(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None

        while self.stitches:
            next = self.stitches.pop()
            if next: next.remove()

class flat(__base):
    def _displace(self, pos):
        return pos + array([0,1,0]) * self._row_height()

    def cast_on(self, N):
        self.stitches.append(None)
        self.turn()

        positions = [array([1,0,0]) * self._stitch_width() * i for i in reversed(range(N))]

        for p in positions: self.create_node(p, 1)

        self.turn()

    def _arrow(self, pos):
        return array([1,0,0]) * self.orientation

    def end_row(self):
        self.turn()

class circle(__base):
    def _displace(self, pos):
        ns = norm(pos)
        if ns == 0:
            raise ValueError
        return pos * (ns + self._row_height()) / ns

    def _arrow(self, pos):
        a = cross(pos, array([0,0,1])) * self.orientation
        na = norm(a)
        if na == 0:
            raise ValueError
        return a / na

    def cast_on(self, N, cinch=False):
        R = N * self._stitch_width() / (2*math.pi)
        positions = [array([math.sin(t),math.cos(t),0])*R for t in [i*math.pi*2/N for i in range(N)]]
        for p in positions:
            self.create_node(p, 1)
            if cinch: self.loose_edge.length *= 0.25

        self.loose_edge.after = self.stitches[-1].before
        self.stitches[-1].before.edges.append(self.loose_edge)
        self.loose_edge = None

class tube(circle):
    def _displace(self, pos):
        return pos + array([0,0,1]) * self._row_height()

    def _relax_nodes(self, working):
        R = len(self.stitches) * self._stitch_width() / (2*math.pi)
        for n in working:
            if n is not None:
                r = norm(cross(n.pos, array([0,0,1])))
                if r == 0:
                    raise ValueError
                n.pos[0:2] *= R / r

        circle._relax_nodes(self, working)
