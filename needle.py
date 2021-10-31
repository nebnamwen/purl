import math
from numpy import array, cross
from numpy.linalg import norm
from collections import deque

from model import node, h_edge, v_edge, over_under_force, force

class needle(object):
    def __init__(self, rpi=5, spi=5, wpi=15, color="gray"):
        self.rpi = rpi
        self.spi = spi
        self.wpi = wpi
        self.color = color

        self.stitches = deque()
        self.loose_edge = None
        self.orientation = 1

    def _row_height(self): return 1.0 / self.rpi
    def _stitch_width(self): return 1.0 / self.spi
    def _yarn_thickness(self): return 1.0 / self.wpi

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

    def _relax(self, N = 1):
        working = []
        interval = 0

        working.append(self.stitches[-1].before if self.stitches[-1] else None)

        i = 0
        while interval < self._stitch_width() * 2 or len(working) < N + 2:
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

    def _create_node(self, ks_norm, pull, push, cls=None):
        inbound = [self.stitches.pop() for i in range(pull)]
        if not inbound:
            if self.loose_edge:
                newpos = self.loose_edge.before.pos
            elif self.stitches and self.stitches[-1]:
                newpos = self._displace(self.stitches[-1].before.pos)
            else:
                raise ValueError
        elif None in inbound:
            raise ValueError
        else:
            newpos = self._displace(sum([s.before.pos for s in inbound]) / len(inbound))

        self._create_node_at(newpos, ks_norm, inbound, push, cls)

    def _create_node_at(self, pos, ks_norm, inbound, push, cls=None):
        new_node = (cls or node)(pos, self.orientation, ks_norm, self.loose_edge, inbound)

        for i in range(push):
            self.stitches.appendleft(v_edge(new_node, self._stitch_width(), self.color, self._yarn_thickness()))

        self.loose_edge = h_edge(new_node, self._stitch_width(), self.color, self._yarn_thickness())

    def _rotate(self, N, M, RL=0):
        working = deque()

        over = []
        under = []

        for i in range(N):
            s = self.stitches.pop()
            if s is None: raise ValueError

            if N - i <= M:
                over.append(s)
            else:
                under.append(s)

            working.appendleft(s)

        working.rotate(M)

        while working:
            self.stitches.append(working.popleft())

        if RL != 0:
            over_under_force(over, under, RL * self.orientation, self._yarn_thickness())

    def turn(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None
        self.stitches.reverse()
        self.orientation *= -1

    def knit(self, N = 1):
        for i in range(N):
            self._create_node(1,1,1)
            self._relax()

    def purl(self, N = 1):
        for i in range(N):
            self._create_node(-1,1,1)
            self._relax()

    def kfab(self):
        self._create_node(1,1,2)
        self._relax()

    def k2tog(self):
        self._create_node(1,2,1)
        self._relax()

    def p2tog(self):
        self._create_node(-1,2,1)
        self._relax()

    def k3tog(self):
        self._create_node(1,3,1)
        self._relax()

    def p3tog(self):
        self._create_node(-1,3,1)
        self._relax()

    def yo(self):
        self._create_node(0,0,1)
        self.stitches[0].length = self._yarn_thickness()
        self._relax()

    def cable(self, NR, NL, KR, KL, RL):
        self._rotate(NR + NL, NL, RL)
        for i in range(NR): self._create_node(1,1,KR)
        for i in range(NL): self._create_node(1,1,KL)
        self._relax(NR + NL)

    def slip(self, N = 1, FB = 0):
        for i in range(N):
            s = self.stitches.pop()
            self.stitches.appendleft(s)
            if self.loose_edge:
                self.loose_edge.length += self._stitch_width()
                if FB:
                    over_under_force([self.loose_edge], [s], FB * self.orientation, self._yarn_thickness())

    def cast_off(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None

        while self.stitches:
            next = self.stitches.pop()
            if next: next.remove()

class tube(needle):
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
