import math
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

    def yo(self):
        self._create_node(0,0,1)
        self.stitches[0].length = self._yarn_thickness()
        self._relax()

    def cable(self, NR, NL, KR, KL, RL):
        self._rotate(NR + NL, NL, RL)
        for i in range(NR): self._create_node(1,1,KR)
        for i in range(NL): self._create_node(1,1,KL)
        self._relax(NR + NL)

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

        down = self.__down()
        up = self.__up()
        before = self.__before()
        after = self.__after()

        h_arrow = self.__h_arrow()
        if h_arrow is not None:
            for e in down:
                delta = h_arrow * h_arrow.dot(e.before.pos - self.pos)
                delta *= 0.1 / len(down)
                forces.append(force(self, delta))
                forces.append(force(e.before, -delta))

            for e in up:
                delta = h_arrow * h_arrow.dot(e.after.pos - self.pos)
                delta *= 0.1 / len(up)
                forces.append(force(self, delta))
                forces.append(force(e.after, -delta))

            if before and after:
                if h_arrow.dot(self.pos - before.before.pos) < 0:
                    delta = 0.1 * h_arrow * h_arrow.dot(before.before.pos - self.pos)
                    forces.append(force(self, delta))
                    forces.append(force(before.before, -delta))

                if h_arrow.dot(after.after.pos - self.pos) < 0:
                    delta = 0.1 * h_arrow * h_arrow.dot(self.pos - after.after.pos)
                    forces.append(force(self, delta))
                    forces.append(force(after.after, -delta))

        v_arrow = self.__v_arrow()
        if v_arrow is not None:
            if before:
                delta = v_arrow * v_arrow.dot(before.before.pos - self.pos)
                delta *= 0.1
                forces.append(force(self, delta))
                forces.append(force(before.before, -delta))

            if after:
                delta = v_arrow * v_arrow.dot(after.after.pos - self.pos)
                delta *= 0.1
                forces.append(force(self, delta))
                forces.append(force(after.after, -delta))

        normal = self.rs_normal()
        if norm(normal) > 0:
            if up and down:
                for e in up + down:
                    n = [ n for n in [e.before, e.after] if n is not self ][0]
                    delta = normal * (normal.dot(n.pos - self.pos) + e.thickness*self.rs_norm*self.ks_norm) * 0.1
                    forces.append(force(self, delta))
                    forces.append(force(n, -delta))

            if before and after:
                for e in [before, after]:
                    n = [ n for n in [e.before, e.after] if n is not self ][0]
                    delta = normal * (normal.dot(n.pos - self.pos) - e.thickness*self.rs_norm*self.ks_norm) * 0.1
                    forces.append(force(self, delta))
                    forces.append(force(n, -delta))

        return forces

    def __get_normal(self, orientation):
        h_arrow = self.__h_arrow()
        v_arrow = self.__v_arrow()
        if None in (h_arrow, v_arrow): return array([0,0,0])

        crs = cross(self.__h_arrow(), self.__v_arrow()) * orientation
        n = norm(crs)
        if n > 0:
            crs /= n
        return crs

    def rs_normal(self): return self.__get_normal(self.rs_norm)

    def ks_normal(self): return self.__get_normal(self.ks_norm)

    def draw(self, disp, full):
        if full:
            edges_to_draw = self.__up() + self.__down()
            if self.__before() is not None: edges_to_draw.append(self.__before())
            if self.__after() is not None: edges_to_draw.append(self.__after())

            ks = disp.m.dot(self.ks_normal())[2]
            if ks < 0: edges_to_draw.reverse()

            for e in edges_to_draw:
                e.draw_half(disp, self)

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
    thick_mult = 0

    def __init__(self, before, length, color, thickness):
        self.before = before
        self.before.edges.append(self)
        self.after = None
        self.length = length
        self.color = color
        self.thickness = thickness
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

    def draw(self, disp, full):
        if self.before and self.after and not full:
            p1 = disp.draw_pos(self.before.pos)
            p2 = disp.draw_pos(self.after.pos)
            disp.canvas.create_line([ tuple(p1), tuple(p2) ],
                                    fill = self.color,
                                    width = (disp.zoom * self.thickness * self.thick_mult)
                                    )

    def draw_half(self, disp, n):
        if self.before and self.after and n in (self.before, self.after):
            p1 = disp.draw_pos(n.pos)
            p2 = disp.draw_pos((self.before.pos + self.after.pos) / 2)
            disp.canvas.create_line([ tuple(p1), tuple(p2) ],
                                    fill = "black",
                                    width = (disp.zoom * self.thickness * self.thick_mult + 1)
                                    )
            disp.canvas.create_line([ tuple(p1), tuple(p2) ],
                                    fill = self.color,
                                    width = (disp.zoom * self.thickness * self.thick_mult - 1)
                                    )
            p1 = disp.draw_pos(0.6*self.before.pos + 0.4*self.after.pos)
            p2 = disp.draw_pos(0.4*self.before.pos + 0.6*self.after.pos)
            disp.canvas.create_line([ tuple(p1), tuple(p2) ],
                                    fill = self.color,
                                    width = (disp.zoom * self.thickness * self.thick_mult - 2)
                                    )

class v_edge(edge):
    thick_mult = 2

class h_edge(edge):
    thick_mult = 1

class over_under_force(object):
    def __init__(self, over, under, normal, thickness):
        self.over = over
        self.under = under
        self.normal = normal
        self.thickness = thickness
        mesh.add(self)

    def draw(self, disp, full):
        pass

    def get_forces(self):
        over_nodes = [ e.before for e in self.over ] + [ e.after for e in self.over ]
        under_nodes = [ e.before for e in self.under ] + [ e.after for e in self.under ]
        all_nodes = over_nodes + under_nodes
        rs_normal = sum([n.rs_normal() for n in all_nodes])
        normal = rs_normal * self.normal

        forces = []

        if norm(normal) > 0:
            normal /= norm(normal)
            avg_dot = sum([n.pos.dot(normal) for n in all_nodes]) / len(all_nodes)

            for n in over_nodes:
                dot = n.pos.dot(normal)
                if dot < avg_dot + self.thickness:
                    delta = normal * (avg_dot + self.thickness - dot) * 0.1
                    forces.append(force(n, delta))

            for n in under_nodes:
                dot = n.pos.dot(normal)
                if dot > avg_dot - self.thickness:
                    delta = normal * (avg_dot - self.thickness - dot) * 0.1
                    forces.append(force(n, delta))

        return forces

class force(object):
    def __init__(self, N, D):
        self.node = N
        self.delta = D

    def apply(self):
        self.node.pos = self.node.pos + self.delta

class display(object):
    def __init__(self):
        self.m = array([[1,0,0],[0,1,0],[0,0,1]])
        self.center = array([100,100])
        self.zoom = 100.0
        self.drag_xy = None
        c = Tkinter.Canvas(width=600, height=600)
        c.pack()

        c.bind("<Button-1>", self.click)
        c.bind("<B1-Motion>", self.drag1)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<Button-2>", self.click)
        c.bind("<B2-Motion>", self.drag2)
        c.bind("<ButtonRelease-2>", self.release)
        c.bind("<Button-3>", self.click)
        c.bind("<B3-Motion>", self.drag3)
        c.bind("<ButtonRelease-3>", self.release)

        self.canvas = c

        self.draw_all(True)

    def run(self):
        self.canvas.mainloop()

    def draw_all(self, full):
        self.canvas.delete("all")
        if full:
            objs = [ n for n in mesh.objects if isinstance(n,node) ]
            objs.sort(key=lambda n: self.m.dot(n.pos)[2])
        else:
            objs = mesh.objects
        for obj in objs:
            obj.draw(self, full)

    def draw_pos(self, pos):
        xyz = self.m.dot(pos)
        return (xyz[0:2]*self.zoom + self.center)

    def click(self, e):
        self.drag_xy = array([e.x, e.y])

    def release(self, e):
        self.drag_xy = None
        self.draw_all(True)

    def _drag_delta(self, e):
        if self.drag_xy is not None:
            new_xy = array([e.x, e.y])
            delta = new_xy - self.drag_xy
            self.drag_xy = new_xy
            return delta
        else:
            return None

    def drag1(self, e):
        delta = self._drag_delta(e)
        if delta is not None:
            self.center += delta
            self.draw_all(False)

    def drag2(self, e):
        delta = self._drag_delta(e)
        if delta is not None:
            self.update_m(delta)
            self.draw_all(False)

    def drag3(self, e):
        delta = self._drag_delta(e)
        if delta is not None:
            newzoom = self.zoom * math.exp(delta[1]*(-0.003))
            if newzoom > 20 and newzoom < 500:
                self.zoom = newzoom
            self.draw_all(False)

    def update_m(self, xy):
        xy = xy / (100.0)

        dx, dy = xy

        T = array([[1,0,dx],[0,1,dy],[-dx,-dy,1]])

        self.m = T.dot(self.m)

        self.m[0] /= norm(self.m[0])

        self.m[2] = cross(self.m[0], self.m[1])
        self.m[2] /= norm(self.m[2])

        self.m[1] = cross(self.m[2], self.m[0])
        self.m[1] /= norm(self.m[1])

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
    def cable(n,m,k):
        mesh.clear()
        N = needle()
        N.cast_on(n*2+4)

        for j in range(k):
            for i in range(m):
                N.knit(n*2+4)
                N.turn()

            N.knit(n)
            N.cable(2,2,1,1,1)
            N.knit(n)
            N.turn()

        for i in range(m):
            N.knit(n*2+4)
            N.turn()

        N.cast_off()
        mesh.relax(40*(n+m))
        display().run()
