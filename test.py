import needles
from lang import *
from abbrev import *
from chart import chart
from display import display

def rect(n, m):
    N = needles.flat()
    N.cast_on(n)
    N.do([ knit(n), turn ] * m)
    N.cast_off()
    N.mesh.relax(10*(n+m))
    display(N.mesh).run()

def srect(n, m):
    N = needles.flat()
    N.cast_on(n)
    N.do([ if_right_side(knit, purl) * n, turn ] * m)
    N.cast_off()
    N.mesh.relax(10*(n+m))
    display(N.mesh).run()

def slrect():
    N = needles.flat()
    N.cast_on(10)
    N.do([ [knit(3), slip(4,wyib), knit(3), turn],
           [purl(10), turn] ] * 7)
    N.cast_off()
    N.mesh.relax(100)
    display(N.mesh).run()

def yorect(n,m):
    N = needles.flat()
    N.cast_on(n+3)

    N.do([[ k1, yo, k2tog, k(n), turn ],
          [ if_right_side(k(n+3), p(n+3)), turn ] * m ])

    N.cast_off()
    N.mesh.relax(5*(n+m))
    display(N.mesh).run()

def cable(n,m,r):
    cable = [ sl_to_cbl(2,front), k2, k2(from_cbl) ]

    ss = [ if_right_side(k,p) ]
    rs = [ if_right_side(p,k) ]

    bg_row = [rs * n, ss * 4, rs * n, turn]

    N = needles.flat()

    N.cast_on(n*2+4)

    N.do(bg_row,
         [ bg_row * (m-1),
           [rs * n, cable, rs * n, turn] ] * r,
         bg_row * m )

    N.cast_off()
    N.mesh.relax(5*(n+m))
    display(N.mesh).run()

def circle(n):
    N = needles.circle()
    N.cast_on(6)

    N.do([[ k, yo, k(i) ] * 6 for i in range(n)])

    N.cast_off()
    N.mesh.relax(5*n)
    display(N.mesh).run()

def sock(m,n):
    N = needles.tube()
    N.cast_on(6,cinch=True)

    N.do([[ kfab, k(i) ] * 6 for i in range(m)],
         [[ k(m+1) ] * 6 for i in range(n)],
         [[ turn, [ if_right_side(p,k) ] * (2*m+2+i) ] for i in range(4)],
         [[ k(m+1) ] * 6 for i in range(n)])

    N.cast_off()
    N.mesh.relax(10*(n+m))
    display(N.mesh).run()

def bobble(n,m,r):
    w = 2*n + 1

    N = needles.flat()
    N.cast_on(w)

    MB = [ into_same_stitch(k1,p1,k1), turn, p(3), turn, k3tog ]

    N.do([[ if_right_side(k,p) ] * w, turn] * m,
         [[ k(n), MB, k(n), turn ],
          [[ if_right_side(k,p) ] * w, turn] * m] * r)

    N.cast_off()
    N.mesh.relax(10*(n+m))
    display(N.mesh).run()

def diamond(n):
    N = needles.flat()
    N.cast_on(3)

    N.do([ [ kfab, k(i+2), turn ] for i in range(n) ],
         [ [ k2tog, k(i+2), turn ] for i in reversed(range(n)) ])

    N.cast_off()
    N.mesh.relax(10*n)
    display(N.mesh).run()

def moss_from_chart(n,m):
    needle = needles.flat()
    needle.cast_on(n*2 + 4)

    key = {
        "k": if_right_side(k,p),
        "p": if_right_side(p,k)
        }

    stockinette = chart(key, "k")

    moss = chart(key, """
k p
p k
""")

    border = stockinette ** (m*2) * 2

    needle.do(border + moss ** m * n + border)

    needle.cast_off()
    needle.mesh.relax(8*(n+m))
    display(needle.mesh).run()

def hat_from_chart():
    needle = needles.tube()
    
    section = chart(
        {
            "k": knit,
            "p": purl,
            "/": k2tog
            },
        """
                     /
                   /  k
                 /  k p
               /  k p k
             /  k p k p
           /  k p k p k
          k k p k p k p
         /  k k p k p k
        k k k p k p k p
       /  k p k p k p k
      k k p k p k p k p
     /  k k p k p k p k
    k k k p k p k p k p
   /  k p k p k p k p k
  k k p k p k p k p k p
 /  k k p k p k p k p k
k k k p k p k p k p k p
k k p k p k p k p k p k
k k k p k p k p k p k p
k k p k p k p k p k p k
k k k p k p k p k p k p
k k p k p k p k p k p k
k k p p k k p p k k p p
k k p p k k p p k k p p
k k p p k k p p k k p p
k k p p k k p p k k p p
k k p p k k p p k k p p
k k p p k k p p k k p p
""")

    needle.cast_on(72)
    needle.do(section * 6)
    needle.cast_off()

    needle.mesh.relax(150)
    display(needle.mesh).run()

def honeycomb(m,n):
    needle = needles.flat()
    needle.cast_on(m*8+6)

    blue = color("blue")

    pattern = [
        [
            [ knit(m*8+6), turn ] * 2,
            [
                blue([ knit(2), [ slip(2,wyib), knit(6) ] * m, slip(2,wyib), knit(2), turn ]),
                blue([ purl(2), [ slip(2,wyif), purl(6) ] * m, slip(2,wyif), purl(2), turn ]),
                ] * 3,
            [ knit(m*8+6), turn ] * 4,
            [
                blue([ knit(6), [ slip(2,wyib), knit(6) ] * m, turn ]),
                blue([ purl(6), [ slip(2,wyif), purl(6) ] * m, turn ]),
                ] * 3,
            ] * n,
        [ knit(m*8+6), turn ] * 2,
        ]

    needle.do(pattern)
    needle.cast_off()

    needle.mesh.relax(20)
    display(needle.mesh).run()
