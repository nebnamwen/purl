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
        return (self._tension_forces() + self._hshear_forces() + self._hfold_forces() +
                self._vshear_forces() + self._flatten_forces()
                )

    def _tension_forces(self):
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

        return forces

    def _hshear_forces(self):
        forces = []

        if norm(self._h_arrow) > 0:
            # correct horizontal shear of vertical edges
            for e in self._down:
                forces.extend(force.dot(e, self._h_arrow, 0, 0.1/len(self._down)))
            for e in self._up:
                forces.extend(force.dot(e, self._h_arrow, 0, 0.1/len(self._up)))

        return forces

    def _hfold_forces(self):
        forces = []

        if norm(self._h_arrow) > 0:
            # correct foldover of horizontal edges
            if self._before and self._after:
                if self._h_arrow.dot(self.pos - self._before.before.pos) < 0:
                    forces.extend(force.dot(self._before, self._h_arrow, 0, 0.1))
                if self._h_arrow.dot(self._after.after.pos - self.pos) < 0:
                    forces.extend(force.dot(self._after, self._h_arrow, 0, 0.1))

        return forces

    def _vshear_forces(self):
        forces = []

        if norm(self._v_arrow) > 0:
            # correct vertical shear of horizontal edges
            if self._before:
                forces.extend(force.dot(self._before, self._v_arrow, 0, 0.1))
            if self._after:
                forces.extend(force.dot(self._after, self._v_arrow, 0, 0.1))

        return forces

    def _flatten_forces(self):
        forces = []

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

        return sum([ e.draw_half_segments(self) for e in edges_to_draw ], [])

    def key_point(self, x_edge, x, y, z):
        bef = self._before.before.pos if self._before and x_edge < 0 else self.pos
        aft = self._after.after.pos if self._after and x_edge > 0 else self.pos
        e = aft - bef

        return (self.pos +
                e * x_edge +
                self._h_arrow * x +
                self._v_arrow * y +
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
            return array([0,0,0])

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
            return array([0,0,0])

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

class yo_node(node):

    def _vshear_forces(self):
        return []

    def get_draw_segments(self, m):
        
        if self._up:
            if len(self._up) == 1:
                e = self._up[0]
            else:
                raise ValueError("yarnover with multiple stitches")
        elif self._after:
            e = self._after
        elif self._before:
            e = self._before
        else:
            raise ValueError("yarnover with no edges")

        th = e.thickness

        segments = []
        points = []

        if self._before:
            bef_bef = self._before.before.key_point(0.25, -0.5*th, -0.5*th, 0.5*th)
            bef_aft = self.key_point(-0.25, 0.5*th, -0.5*th, 0.5*th)

            points.extend([ (bef_bef + bef_aft)/2, (bef_bef*3 + bef_aft*5)/8 ])
        else:
            points.append(self.pos)

        if self._up:
            twist = self.rs_norm * self._up[0].after.rs_norm

            p1 = self.key_point(-0.25, 0.5*th, -0.5*th, -0.5*th)
            p2 = self._up[0].after.key_point(-0.25*twist, -0.5*th*twist, 0.5*th, 0)
            p3 = self._up[0].after.key_point(0.25*twist, 0.5*th*twist, 0.5*th, 0)
            p4 = self.key_point(0.25, -0.5*th, -0.5*th, -0.5*th)

            points.extend([(5*p1 + 3*p2)/8, (3*p1 + 5*p2)/8])
            segments.append(draw_segment(points, e.color, e.thickness))
            points = [(5*p3 + 3*p4)/8, (3*p3 + 5*p4)/8]

        if self._after:
            aft_bef = self.key_point(0.25, -0.5*th, -0.5*th, 0.5*th)
            aft_aft = self._after.after.key_point(-0.25, 0.5*th, -0.5*th, 0.5*th)

            points.extend([ (5*aft_bef + 3*aft_aft)/8, (aft_bef + aft_aft)/2 ])
        else:
            points.append(self.pos)

        segments.append(draw_segment(points, e.color, e.thickness))

        return segments

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

    def draw_half_segments(self, n):
        return []

class v_edge(edge):
    thick_mult = 2

    def draw_half_segments(self, n):
        if self.before and self.after and n in (self.before, self.after):
            th = self.thickness
            bn = self.before.rs_norm
            an = self.after.rs_norm

            p1 = self.before.key_point(-0.25*bn, 0.5*th*bn, -0.5*th, -0.5*th)
            p2 = self.after.key_point(-0.25*an, -0.5*th*an, 0.5*th, 0)
            p3 = self.after.key_point(0.25*an, 0.5*th*an, 0.5*th, 0)
            p4 = self.before.key_point(0.25*bn, -0.5*th*bn, -0.5*th, -0.5*th)

            if n is self.before:
                return [
                    draw_segment([p1, p1, (5*p1 + 3*p2)/8, (3*p1 + 5*p2)/8], self.color, self.thickness),
                    draw_segment([p4, p4, (3*p3 + 5*p4)/8, (5*p3 + 3*p4)/8], self.color, self.thickness)
                    ]
            else:
                return [
                    draw_segment([(5*p1 + 3*p2)/8, (3*p1 + 5*p2)/8, p2, p3, (5*p3 + 3*p4)/8, (3*p3 + 5*p4)/8], self.color, self.thickness)
                    ]

class h_edge(edge):
    thick_mult = 1

    def draw_half_segments(self, n):
        if self.before and self.after and n in (self.before, self.after):
            th = self.thickness
            bef = self.before.key_point(0.25, -0.5*th, -0.5*th, 0.5*th)
            aft = self.after.key_point(-0.25, 0.5*th, -0.5*th, 0.5*th)

            p1 = bef if n is self.before else aft
            p2 = (bef + aft) / 2
            return [ draw_segment([p1, p1, p2], self.color, self.thickness) ]

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
