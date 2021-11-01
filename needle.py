import math
from numpy import array, cross
from numpy.linalg import norm
from collections import deque

from model import node, h_edge, v_edge, crossover, force

class __base(object):
    def __init__(self, rpi=5, spi=5, wpi=15, color="gray"):
        self.rpi = rpi
        self.spi = spi
        self.wpi = wpi
        self.color = color

        self.stitches = deque()
        self.loose_edge = None
        self.orientation = 1

        self.cable_stitches = deque()
        self.cable_side = None

        self._to_be_relaxed = 0

    def _row_height(self): return 1.0 / self.rpi
    def _stitch_width(self): return 1.0 / self.spi
    def _yarn_thickness(self): return 1.0 / self.wpi

    def _displace(self, pos):
        raise NotImplemented

    def cast_on(self, N):
        raise NotImplemented

    def _arrow(self, pos):
        raise NotImplemented

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
                crossover(s, cs, self.cable_side * self.orientation, self._yarn_thickness())

    def _create_node(self, ks_norm, pull, push, from_cable=False, cls=None):
        inbound = [self._pop_stitch(from_cable) for i in range(pull)]
        if not inbound:
            if self.loose_edge:
                newpos = self.loose_edge.before.pos
            elif self.stitches and self.stitches[-1]:
                newpos = self._displace(self.stitches[-1].before.pos)
            else:
                raise ValueError
        else:
            newpos = self._displace(sum([s.before.pos for s in inbound]) / len(inbound))

        self._create_node_at(newpos, ks_norm, inbound, push, from_cable, cls)

        self._to_be_relaxed += 1
        self._relax()

    def _create_node_at(self, pos, ks_norm, inbound, push, from_cable=False, cls=None):
        new_node = (cls or node)(pos, self.orientation, ks_norm, self.loose_edge, inbound)

        for i in range(push):
            self._push_stitch(v_edge(new_node, self._stitch_width(), self.color, self._yarn_thickness()), from_cable)

        self.loose_edge = h_edge(new_node, self._stitch_width(), self.color, self._yarn_thickness())

    def slip_to_cable(self, N, FB=0):
        if N > 0:
            for i in range(N):
                self.cable_stitches.appendleft(self._pop_stitch())
            self.cable_side = FB

    def turn(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None
        self.stitches.reverse()
        self.orientation *= -1

    def knit(self, N = 1):
        for i in range(N):
            self._create_node(1,1,1)

    def purl(self, N = 1):
        for i in range(N):
            self._create_node(-1,1,1)

    def kfab(self):
        self._create_node(1,1,2)

    def k2tog(self):
        self._create_node(1,2,1)

    def p2tog(self):
        self._create_node(-1,2,1)

    def k3tog(self):
        self._create_node(1,3,1)

    def p3tog(self):
        self._create_node(-1,3,1)

    def yo(self):
        self._create_node(0,0,1)
        self.stitches[0].length = self._yarn_thickness()
        self._relax()

    def cable(self, NR, NL, KPR, KPL, FB):
        self.slip_to_cable(NL, FB)
        for i in range(NR): self._create_node(KPR,1,1)
        for i in range(NL): self._create_node(KPL,1,1,from_cable=True)

    def slip(self, N = 1, FB = 0):
        for i in range(N):
            s = self._pop_stitch()
            self._push_stitch(s)
            if self.loose_edge:
                self.loose_edge.length += self._stitch_width()
                if FB:
                    crossover(self.loose_edge, s, FB * self.orientation, self._yarn_thickness())

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

        for p in positions: self._create_node_at(p, 0, [], 1)

        self.turn()

    def _arrow(self, pos):
        return array([1,0,0]) * self.orientation

class tube(__base):
    def _displace(self, pos):
        return pos + array([0,0,1]) * self._row_height()

    def _arrow(self, pos):
        a = cross(pos, array([0,0,1])) * self.orientation
        na = norm(a)
        if na == 0:
            raise ValueError
        return a / na

    def cast_on(self, N, circum=None, cinch=False):
        if circum is None: circum = N
        R = circum * self._stitch_width() / (2*math.pi)
        positions = [array([math.sin(t),math.cos(t),0])*R for t in [i*math.pi*2/N for i in range(N)]]
        for p in positions:
            self._create_node_at(p, 0, [], 1)
            if cinch: self.loose_edge.length *= 0.25

        self.loose_edge.after = self.stitches[-1].before
        self.stitches[-1].before.edges.append(self.loose_edge)
        self.loose_edge = None

class circle(tube):
    def _displace(self, pos):
        ns = norm(pos)
        if ns == 0:
            raise ValueError
        return pos * (ns + self._row_height()) / ns

    def cast_on(self, N):
        tube.cast_on(self, N, cinch=True)
