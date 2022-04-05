import math
from numpy import array, array_equal, cross
from numpy.linalg import norm
import tkinter

class display(object):
    def __init__(self, mesh):
        self.mesh = mesh
        self.m = array([[1,0,0],[0,1,0],[0,0,1]])
        self.center = array([300,300])
        self.zoom = 100.0
        self.drag_xy = None
        c = tkinter.Canvas(width=600, height=600)
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

        self.mesh.cook_vectors(True)

        self.draw_all(True)

    def run(self):
        self.canvas.mainloop()

    def draw_all(self, full):
        self.canvas.delete("all")
        objs = [ n for n in self.mesh.objects if n.pos is not None ]
        if full:
            objs.sort(key=lambda n: -self.m.dot(n.pos)[2])
        for obj in objs:
            for s in obj.get_draw_segments(self.m):
                self.draw_segment(s, full)

    def draw_segment(self, s, full):
        points = s.points
        dots = []
        for i in (1, -1):
            if array_equal(points[i], points[i-1]):
                dots.append(self.draw_pos(points.pop(i)))
        points = [ self.draw_pos(p) for p in points ]
        
        if full:
            for d in dots:
                self.canvas.create_line([d, d],
                                        fill = "black",
                                        width = (self.zoom * s.thickness + 1),
                                        capstyle=tkinter.ROUND
                                        )
            self.canvas.create_line(points,
                                    fill = "black",
                                    width = (self.zoom * s.thickness + 1)
                                    )
        self.canvas.create_line(points,
                                fill = s.color,
                                width = (self.zoom * s.thickness - 1)
                                )
        for d in dots:
            self.canvas.create_line([d, d],
                                    fill = s.color,
                                    width = (self.zoom * s.thickness - 1),
                                    capstyle=tkinter.ROUND
                                    )

    def draw_pos(self, pos):
        xyz = self.m.dot(pos)
        return tuple(-xyz[0:2]*self.zoom + self.center)

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
