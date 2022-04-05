from numpy import array, cross
from numpy.linalg import norm
from math import exp, log, sin, atan

class mesh(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

    def relax(self, N=1):
        self.cook_vectors(True)

        for i in range(N):
            forces = []

            for obj in self.objects:
                forces.extend(obj.get_forces())

            for f in forces:
                f.apply()

            self.cook_vectors()

    def center_all(self, C=array([0,0,0])):
        nodes = [ n for n in self.objects if n.pos is not None ]
        center = sum([n.pos for n in nodes]) / len(nodes)
        forces = [ force(n,-center+C) for n in nodes ]
        
        for f in forces:
            f.apply()

    def cook_vectors(self, topo=False):
        for n in self.objects:
            n.cook_vectors(topo)

class meshobject(object):
    def __init__(self, msh):
        self.pos = None
        self.mesh = msh
        self.mesh.add(self)

    def get_forces(self):
        return []

    def get_draw_segments(self, m):
        return []

    def cook_vectors(self, topo=False):
        pass

class node(meshobject):
    def __init__(self, msh, pos, rs_norm, ks_norm, before, below):
        meshobject.__init__(self, msh)
        self.pos = pos
        self.rs_norm = rs_norm
        self.ks_norm = ks_norm
        self.edges = [before] if before else []
        self.edges.extend(below)
        for e in self.edges: e.after = self

    def get_forces(self):
        forces = []

        # stretch horizontally/vertically
        tension_edges = [ e for e in [self._before] + self._up + [self._after] if e is not None ]
        tension_length = sum([ e.length * e.thick_mult for e in tension_edges ])
        tension_actual = sum([ norm(e.after.pos - e.before.pos) * e.thick_mult for e in tension_edges ])
        tension_ratio = tension_actual / tension_length
        # print(tension_ratio)
        tension_ratio = exp(0.5*sin(atan(log(tension_ratio))))

        for e in tension_edges:
            delta = e.after.pos - e.before.pos
            forces.extend(force.dot(e, delta, norm(delta) / tension_ratio, 0.25))

        if self._h_arrow is not None:
            # correct horizontal shear of vertical edges
            for e in self._down:
                forces.extend(force.dot(e, self._h_arrow, 0, 0.1/len(self._down)))
            for e in self._up:
                forces.extend(force.dot(e, self._h_arrow, 0, 0.1/len(self._up)))

            # correct foldover of horizontal edges
            if self._before and self._after:
                if self._h_arrow.dot(self.pos - self._before.before.pos) < 0:
                    forces.extend(force.dot(self._before, self._h_arrow, 0, 0.1))
                if self._h_arrow.dot(self._after.after.pos - self.pos) < 0:
                    forces.extend(force.dot(self._after, self._h_arrow, 0, 0.1))

        if self._v_arrow is not None:
            # correct vertical shear of horizontal edges
            if self._before:
                forces.extend(force.dot(self._before, self._v_arrow, 0, 0.1))
            if self._after:
                forces.extend(force.dot(self._after, self._v_arrow, 0, 0.1))                

        normal = self.rs_normal()
        nsign = self.rs_norm*self.ks_norm
        # align all edges with the plane of the node, with an offset for knit/purl curl moment
        if self._up and self._down:
            for e in self._up:
                forces.extend(force.dot(e, normal, -nsign*e.thickness, 0.1))
            for e in self._down:
                forces.extend(force.dot(e, normal, nsign*e.thickness, 0.1))
        if self._before and self._after:
            forces.extend(force.dot(self._before, normal, -nsign*self._before.thickness, 0.1))
            forces.extend(force.dot(self._after, normal, nsign*self._after.thickness, 0.1))

        return forces

    def __get_normal(self, orientation):
        if self._h_arrow is None or self._v_arrow is None: return array([0,0,0])

        crs = cross(self._h_arrow, self._v_arrow) * orientation
        n = norm(crs)
        if n > 0:
            crs /= n
        return crs

    def rs_normal(self): return self.__get_normal(self.rs_norm)

    def ks_normal(self): return self.__get_normal(self.ks_norm)

    def get_draw_segments(self, m):
        edges_to_draw = self._up + self._down
        if self._before is not None: edges_to_draw.append(self._before)
        if self._after is not None: edges_to_draw.append(self._after)

        ks = m.dot(self.ks_normal())[2]
        if ks > 0: edges_to_draw.reverse()

        return [ e.draw_half_segment(self) for e in edges_to_draw ]

    def key_point(self, x_edge, x, y, z):
        return (self.pos +
                e * x_edge +
                self.__h_arrow() * x +
                self.__v_arrow() * y +
                self.ks_normal() * z)

    def cook_vectors(self, topo=False):
        if topo:
            self._before = self.__before()
            self._after = self.__after()

            self._up = self.__up()
            self._down = self.__down()

        self._h_arrow = self.__h_arrow()
        self._v_arrow = self.__v_arrow()

    def __h_arrow(self):
        bef = self._before.before.pos if self._before else self.pos
        aft = self._after.after.pos if self._after else self.pos
        arrow = aft - bef
        n = norm(arrow)
        
        if n > 0:
            arrow /= n
            return arrow
        else:
            return None

    def __v_arrow(self):
        up = self._up
        down = self._down

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

class edge(meshobject):
    thick_mult = 0

    def __init__(self, msh, before, length, color, thickness):
        meshobject.__init__(self, msh)
        self.before = before
        self.before.edges.append(self)
        self.after = None
        self.length = length
        self.color = color
        self.thickness = thickness

    def remove(self):
        if self.before: self.before.edges.remove(self)
        if self.after: self.after.edges.remove(self)
        self.mesh.remove(self)

    def get_forces(self):
        return force.dot(self, self.after.pos - self.before.pos, self.length, 0.1)

    def draw_half_segment(self, n):
        if self.before and self.after and n in (self.before, self.after):
            p1 = n.pos
            p2 = (self.before.pos + self.after.pos) / 2
            return draw_segment([p1, p1, p2], self.color, self.thickness * self.thick_mult)

class v_edge(edge):
    thick_mult = 2

class h_edge(edge):
    thick_mult = 1

class draw_segment(object):
    def __init__(self, points, color, thickness):
        self.points = points
        self.color = color
        self.thickness = thickness

class crossover(meshobject):
    def __init__(self, msh, over, under, normal, thickness):
        meshobject.__init__(self, msh)
        self.over = over
        self.under = under
        self.normal = normal
        self.thickness = thickness

    def draw(self, disp, full):
        pass

    def get_forces(self):
        over_nodes = [ self.over.before, self.over.after ]
        under_nodes = [ self.under.before, self.under.after ]
        all_nodes = over_nodes + under_nodes
        rs_normal = sum([n.rs_normal() for n in all_nodes])

        normal = rs_normal * self.normal

        forces = []

        if norm(normal) > 0:

            normal /= norm(normal)

            over_dot = sum([n.pos.dot(normal) for n in over_nodes]) / 2
            under_dot = sum([n.pos.dot(normal) for n in under_nodes]) / 2

            if over_dot - under_dot < self.thickness:
                delta = self.thickness + under_dot - over_dot
                for n in over_nodes:
                    forces.append(force(n, delta * normal * 0.1))
                for n in under_nodes:
                    forces.append(force(n, -delta * normal * 0.1))

        return forces

class force(object):
    def __init__(self, N, D):
        self.node = N
        self.delta = D

    def apply(self):
        self.node.pos = self.node.pos + self.delta

    @classmethod
    def dot(cls, e, arrow, offset, strength):
        n = norm(arrow)
        if n > 0:
            arrow = arrow / n
            delta = arrow * (arrow.dot(e.after.pos - e.before.pos) - offset) * strength
            return [ cls(e.before, delta), cls(e.after, -delta) ]
        else:
            return []
