import numpy
from numpy import array, cross
from numpy.linalg import norm
import Tkinter
from collections import deque

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
            self.stitches.appendleft(v_edge(new_node, self._stitch_width(), self.color))

        self.loose_edge = h_edge(new_node, self._stitch_width(), self.color)

    def _rotate(self, N, M):
        working = deque()

        for i in range(N):
            s = self.stitches.pop()
            if s is None: raise ValueError
            working.appendleft(s)

        working.rotate(M)

        while working:
            self.stitches.append(working.popleft())

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

    def yo(self):
        self._create_node(0,0,1)
        self.stitches[0].length = self._yarn_thickness()
        self._relax()

    def cbl4(self):
        self._rotate(4,2)
        for i in range(4): self._create_node(1,1,1)
        self._relax(4)

    def cast_off(self):
        if self.loose_edge:
            self.loose_edge.remove()
            self.loose_edge = None

        while self.stitches:
            next = self.stitches.pop()
            if next: next.remove()

class _mesh(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

    def perturb(self, delta):
        for obj in self.objects:
            if isinstance(obj, node):
                obj.pos = obj.pos + delta * 2 * (numpy.random.sample((3,)) - 0.5)
                obj.pos[2] = 0

    def relax(self, N=1):
        for i in range(N):
            forces = []
            for obj in self.objects:
                forces.extend(obj.get_forces())
            for f in forces:
                f.apply()

mesh = _mesh()

class node(object):
    def __init__(self, pos, rs_norm, ks_norm, before, below):
        self.pos = pos
        self.rs_norm = rs_norm
        self.ks_norm = ks_norm
        self.edges = [before] if before else []
        self.edges.extend(below)
        for e in self.edges: e.after = self
        mesh.add(self)

    def get_forces(self):
        forces = []

        h_arrow = self.__h_arrow()
        if h_arrow is not None:
            down = self.__down()
            for e in down:
                delta = h_arrow * h_arrow.dot(e.before.pos - self.pos)
                delta *= 0.1 / len(down)
                forces.append(force(self, delta))
                forces.append(force(e.before, -delta))

            up = self.__up()
            for e in up:
                delta = h_arrow * h_arrow.dot(e.after.pos - self.pos)
                delta *= 0.1 / len(up)
                forces.append(force(self, delta))
                forces.append(force(e.after, -delta))

        v_arrow = self.__v_arrow()
        if v_arrow is not None:
            before = self.__before()
            if before:
                delta = v_arrow * v_arrow.dot(before.before.pos - self.pos)
                delta *= 0.1
                forces.append(force(self, delta))
                forces.append(force(before.before, -delta))

            after = self.__after()
            if after:
                delta = v_arrow * v_arrow.dot(after.after.pos - self.pos)
                delta *= 0.1
                forces.append(force(self, delta))
                forces.append(force(after.after, -delta))

        return forces

    def __get_normal(self, orientation):
        h_arrow = self.__h_arrow()
        v_arrow = self.__v_arrow()
        if None in (h_arrow, v_arrow): return None

        crs = cross(self.__h_arrow(), self.__v_arrow()) * orientation
        n = norm(crs)
        if n > 0:
            crs /= n
            return crs
        else:
            return None

    def rs_normal(self): return self.__get_normal(self.rs_norm)

    def ks_normal(self): return self.__get_normal(self.ks_norm)

    def draw(self, disp):
        pass

    def __h_arrow(self):
        before = self.__before()
        after = self.__after()
        bef = before.before.pos if before else self.pos
        aft = after.after.pos if after else self.pos
        arrow = aft - bef
        n = norm(arrow)
        
        if n > 0:
            arrow /= n
            return arrow
        else:
            return None

    def __v_arrow(self):
        up = self.__up()
        down = self.__down()

        upos = sum([e.after.pos for e in up]) / len(up) if up else self.pos
        dpos = sum([e.before.pos for e in down]) / len(down) if down else self.pos
        arrow = upos - dpos
        n = norm(arrow)

        if n > 0:
            arrow /= n
            return arrow
        else:
            return None

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
        ns = norm(s)
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

class test:
    @staticmethod
    def rect(n, m):
        mesh.clear()
        N = needle()
        N.cast_on(n)
        for i in range(m):
            N.knit(n)
            N.turn()
        N.cast_off()
        mesh.relax(10*(n+m))
        display().run()

    @staticmethod
    def srect(n, m):
        mesh.clear()
        N = needle()
        N.cast_on(n)
        for i in range(m):
            N.knit(n)
            N.turn()
            N.purl(n)
            N.turn()
        N.cast_off()
        mesh.relax(10*(n+m))
        display().run()

    @staticmethod
    def k2togyo(n,m):
        mesh.clear()
        N = needle()
        N.cast_on(n*2+2)

        for i in range(m):
            N.knit(n*2+2)
            N.turn()

        N.knit(n)
        N.k2tog()
        N.yo()
        N.knit(n)
        N.turn()

        for i in range(m):
            N.knit(n*2+2)
            N.turn()

        N.cast_off()
        mesh.relax(40*(n+m))
        display().run()

    @staticmethod
    def cbl4(n,m,k):
        mesh.clear()
        N = needle()
        N.cast_on(n*2+4)

        for j in range(k):
            for i in range(m):
                N.knit(n*2+4)
                N.turn()

            N.knit(n)
            N.cbl4()
            N.knit(n)
            N.turn()

        for i in range(m):
            N.knit(n*2+4)
            N.turn()

        N.cast_off()
        mesh.relax(40*(n+m))
        display().run()
