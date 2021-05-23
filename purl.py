import numpy
from numpy import array
import Tkinter
from collections import deque

class needle(object):
    def __init__(self, rpi=5, spi=5, wpi=12, color="gray"):
        self.rpi = rpi
        self.spi = spi
        self.wpi = wpi
        self.color = color

        self.stitches = deque()
        self.loose_edge = None

    def _row_height(self): return 1.0 / self.rpi
    def _stitch_width(self): return 1.0 / self.spi
    def _yarn_thickness(self): return 1.0 / self.wpi

    def _displace(self, pos):
        return pos + array([0,1,0]) * self._row_height()

    def cast_on(self, N):
        self.stitches.append(None)

        interval = [array([1,0,0]) * self._stitch_width() * i for i in range(N)]

        for p in interval: self._create_node_at(p, [], 1)

        self.turn()

    def _create_node(self, pull, push):
        inbound = [self.stitches.pop() for i in range(pull)]
        if not inbound: raise ValueError # need to fix this to do yarnovers
        if None in inbound: raise ValueError

        newpos = self._displace(sum([s.before.pos for s in inbound]) / len(inbound))
        self._create_node_at(newpos, inbound, push)

    def _create_node_at(self, pos, inbound, push):
        new_node = node(pos, self.loose_edge, inbound)

        for i in range(push):
            self.stitches.appendleft(v_edge(new_node, self._stitch_width(), self.color))

        self.loose_edge = h_edge(new_node, self._stitch_width(), self.color)

    def turn(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None
        self.stitches.reverse()

    def knit(self, N = 1):
        for i in range(N):
            self._create_node(1,1)

    def kfab(self):
        self._create_node(1,2)

    def k2tog(self):
        self._create_node(2,1)

    def cbl4(self):
        self._rotate(4,2)
        for i in range(4): self._create_node(1,1)

    def cast_off(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None

        while self.stitches:
            next = self.stitches.pop()
            if next: next.remove()

class _mesh(object):
    def __init__(self): self.objects = []

    def add(self, obj): self.objects.append(obj)

    def remove(self, obj): self.objects.remove(obj)

    def perturb(self, delta):
        for obj in self.objects:
            if isinstance(obj, node):
                obj.pos = obj.pos + delta * 2 * (numpy.random.sample((3,)) - 0.5)
                obj.pos[2] = 0

    def relax(self, N=1):
        for i in range(N):
            forces = []
            for obj in self.objects: forces.extend(obj.get_forces())
            for f in forces: f.apply()

mesh = _mesh()

class node(object):
    def __init__(self, pos, before, below):
        self.pos = pos
        self.edges = [before] if before else []
        self.edges.extend(below)
        for e in self.edges: e.after = self
        mesh.add(self)

    def get_forces(self):
        return []

    def draw(self, disp):
        pass

    def __before(self):
        all_before = [e for e in self.edges if isinstance(e, h_edge) and e.after is self]
        if all_before: return all_before[0]
        else: return None

    def __after(self):
        all_after = [e for e in self.edges if isinstance(e, h_edge) and e.before is self]
        if all_after: return all_after[0]
        else: return None

    def __down(self):
        return [e for e in self.edges if isinstance(e, v_edge) and e.after is self]

    def __up(self):
        return [e for e in self.edges if isinstance(e, v_edge) and e.before is self]

class edge(object):
    def __init__(self, before, length, color):
        self.before = before
        self.before.edges.append(self)
        self.after = None
        self.length = length
        self.color = color
        mesh.add(self)

    def remove(self):
        if self.before: self.before.edges.remove(self)
        if self.after: self.after.edges.remove(self)
        mesh.remove(self)

    def get_forces(self):
        s = self.before.pos - self.after.pos
        ns = numpy.linalg.norm(s)
        n = s / ns if ns > 0 else array([0,0,0])
        delta = self.length - ns
        return [ force( self.before, n * delta * 0.25 ),
                 force( self.after, n * delta * -0.25 )
                 ]

    def draw(self, disp):
        if self.before and self.after:
            p1 = disp.draw_pos(self.before.pos)
            p2 = disp.draw_pos(self.after.pos)
            disp.canvas.create_line([ tuple(p1), tuple(p2) ],
                                    fill = self.color, width = 2
                                    )
        else:
            if self.before:
                p1 = disp.draw_pos(self.before.pos)
                disp.canvas.create_oval([ tuple(p1 - array([2,2])), tuple(p1 + array([2,2])) ],
                                        fill = "red"
                                        )

class v_edge(edge):
    pass

class h_edge(edge):
    pass

class force(object):
    def __init__(self, N, D):
        self.node = N
        self.delta = D

    def apply(self):
        self.node.pos = self.node.pos + self.delta

class display(object):
    def __init__(self):
        self.transform = array([[1,0,0],[0,1,0],[0,0,1]])
        self.center = array([100,100])
        self.canvas = Tkinter.Canvas(width=600, height=600)
        self.canvas.pack()
        self.draw_all()

    def run(self):
        self.canvas.mainloop()

    def draw_all(self):
        self.canvas.delete("all")
        for obj in mesh.objects:
            obj.draw(self)

    def draw_pos(self, pos):
        xyz = self.transform.dot(pos)
        return (xyz[0:2]*100 + self.center)
