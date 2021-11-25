import needles
from lang import *
from abbrev import *
from model import mesh
from display import display

def rect(n, m):
    mesh.clear()
    N = needles.flat()
    N.cast_on(n)
    N.do([ knit(n), turn ] * m)
    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def srect(n, m):
    mesh.clear()
    N = needles.flat()
    N.cast_on(n)
    N.do([ if_right_side(knit(n), purl(n)), turn ] * m)
    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def slrect():
    mesh.clear()
    N = needles.flat()
    N.cast_on(10)
    N.do([ [knit(3), slip(4,wyib), knit(3), turn],
           [purl(10), turn] ] * 7)
    N.cast_off()
    mesh.relax(100)
    display().run()

def yorect(n,m):
    mesh.clear()
    N = needles.flat()
    N.cast_on(n+3)

    N.do([[ k1, yo, k2tog, k(n), turn ],
          [ if_right_side(k(n+3), p(n+3)), turn ] * m ])

    N.cast_off()
    mesh.relax(5*(n+m))
    display().run()

def cable(n,m,r):
    cable = [ sl_to_cbl(2,front), k2, k2(from_cbl) ]

    ss = [ if_right_side(k,p) ]
    rs = [ if_right_side(p,k) ]

    bg_row = [rs * n, ss * 4, rs * n, turn]

    mesh.clear()
    N = needles.flat()

    N.cast_on(n*2+4)

    N.do(bg_row,
         [ bg_row * (m-1),
           [rs * n, cable, rs * n, turn] ] * r,
         bg_row * m )

    N.cast_off()
    mesh.relax(5*(n+m))
    display().run()

def circle(n):
    mesh.clear()
    N = needles.circle()
    N.cast_on(6)

    N.do([[ k, yo, k(i) ] * 6 for i in range(n)])

    N.cast_off()
    mesh.relax(5*n)
    display().run()

def sock(m,n):
    mesh.clear()
    N = needles.tube()
    N.cast_on(6,cinch=True)

    N.do([[ kfab, k(i) ] * 6 for i in range(m)],
         [[ k(m+1) ] * 6 for i in range(n)],
         [[ turn, [ if_right_side(p,k) ] * (2*m+2+i) ] for i in range(4)],
         [[ k(m+1) ] * 6 for i in range(n)])

    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def bobble(n,m,r):
    w = 2*n + 1
    mesh.clear()
    N = needles.flat()
    N.cast_on(w)

    MB = [ into_same_stitch(k1,p1,k1), turn, p(3), turn, k3tog ]

    N.do([[ if_right_side(k,p) ] * w, turn] * m,
         [[ k(n), MB, k(n), turn ],
          [[ if_right_side(k,p) ] * w, turn] * m] * r)

    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def diamond(n):
    mesh.clear()
    N = needles.flat()
    N.cast_on(3)

    N.do([ [ kfab, k(i+2), turn ] for i in range(n) ],
         [ [ k2tog, k(i+2), turn ] for i in reversed(range(n)) ])

    N.cast_off()
    mesh.relax(10*n)
    display().run()
