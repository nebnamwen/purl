from numpy import array, cross
from numpy.linalg import norm

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

class meshobject(object):
    def __init__(self):
        self.pos = None
        mesh.add(self)

    def get_forces(self):
        return []

    def get_draw_segments(self, m):
        return []

class node(meshobject):
    def __init__(self, pos, rs_norm, ks_norm, before, below):
        meshobject.__init__(self)
        self.pos = pos
        self.rs_norm = rs_norm
        self.ks_norm = ks_norm
        self.edges = [before] if before else []
        self.edges.extend(below)
        for e in self.edges: e.after = self

    def get_forces(self):
        forces = []

        down = self.__down()
        up = self.__up()
        before = self.__before()
        after = self.__after()

        h_arrow = self.__h_arrow()
        if h_arrow is not None:
            # correct horizontal shear of vertical edges
            for e in down:
                forces.extend(force.dot(e, h_arrow, 0, 0.1/len(down)))
            for e in up:
                forces.extend(force.dot(e, h_arrow, 0, 0.1/len(up)))

            # correct foldover of horizontal edges
            if before and after:
                if h_arrow.dot(self.pos - before.before.pos) < 0:
                    forces.extend(force.dot(before, h_arrow, 0, 0.1))
                if h_arrow.dot(after.after.pos - self.pos) < 0:
                    forces.extend(force.dot(after, h_arrow, 0, 0.1))

        v_arrow = self.__v_arrow()
        if v_arrow is not None:
            # correct vertical shear of horizontal edges
            if before:
                forces.extend(force.dot(before, v_arrow, 0, 0.1))
            if after:
                forces.extend(force.dot(after, v_arrow, 0, 0.1))                

        normal = self.rs_normal()
        nsign = self.rs_norm*self.ks_norm
        # align all edges with the plane of the node, with an offset for knit/purl curl moment
        if up and down:
            for e in up:
                forces.extend(force.dot(e, normal, -nsign*e.thickness, 0.1))
            for e in down:
                forces.extend(force.dot(e, normal, nsign*e.thickness, 0.1))
        if before and after:
            forces.extend(force.dot(before, normal, -nsign*before.thickness, 0.1))
            forces.extend(force.dot(after, normal, nsign*after.thickness, 0.1))

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

    def get_draw_segments(self, m):
        edges_to_draw = self.__up() + self.__down()
        if self.__before() is not None: edges_to_draw.append(self.__before())
        if self.__after() is not None: edges_to_draw.append(self.__after())

        ks = m.dot(self.ks_normal())[2]
        if ks > 0: edges_to_draw.reverse()

        return [ e.draw_half_segment(self) for e in edges_to_draw ]

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

class edge(meshobject):
    thick_mult = 0

    def __init__(self, before, length, color, thickness):
        meshobject.__init__(self)
        self.before = before
        self.before.edges.append(self)
        self.after = None
        self.length = length
        self.color = color
        self.thickness = thickness

    def remove(self):
        if self.before: self.before.edges.remove(self)
        if self.after: self.after.edges.remove(self)
        mesh.remove(self)

    def get_forces(self):
        return force.dot(self, self.after.pos - self.before.pos, self.length, 0.25)

    def draw_half_segment(self, n):
        if self.before and self.after and n in (self.before, self.after):
            p1 = n.pos
            p2 = (self.before.pos + self.after.pos) / 2
            return draw_segment(p1, p2, self.color, self.thickness * self.thick_mult)

class v_edge(edge):
    thick_mult = 2

class h_edge(edge):
    thick_mult = 1

class draw_segment(object):
    def __init__(self, p1, p2, color, thickness):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.thickness = thickness

class crossover(meshobject):
    def __init__(self, over, under, normal, thickness):
        meshobject.__init__(self)
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

    @classmethod
    def dot(cls, e, arrow, offset, strength):
        n = norm(arrow)
        if n > 0:
            arrow = arrow / n
            delta = arrow * (arrow.dot(e.after.pos - e.before.pos) - offset) * strength
            return [ cls(e.before, delta), cls(e.after, -delta) ]
        else:
            return []
