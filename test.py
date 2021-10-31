import needle
from model import mesh
from display import display

def rect(n, m):
    mesh.clear()
    N = needle.flat()
    N.cast_on(n)
    for i in range(m):
        N.knit(n)
        N.turn()
    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def srect(n, m):
    mesh.clear()
    N = needle.flat()
    N.cast_on(n)
    for i in range(m):
        N.knit(n)
        N.turn()
        N.purl(n)
        N.turn()
    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def slrect():
    mesh.clear()
    N = needle.flat()
    N.cast_on(10)
    for i in range(7):
        N.knit(3); N.slip(4,1); N.knit(3); N.turn()
        N.purl(10); N.turn()
        
    N.cast_off()
    mesh.relax(100)
    display().run()

def yorect(n,m):
    mesh.clear()
    N = needle.flat()
    N.cast_on(n+3)
    N.knit(); N.yo(); N.k2tog(); N.knit(n); N.turn()

    for i in range(m):
        N.purl(n+3); N.turn()
        N.knit(n+3); N.turn()

    N.cast_off()
    mesh.relax(5*(n+m))
    display().run()

def k2togyo(n,m):
    mesh.clear()
    N = needle.flat()
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

def cable(n,m,k):
    mesh.clear()
    N = needle.flat()
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
    mesh.relax(5*(n+m))
    display().run()

def rscable(n,m,k):
    mesh.clear()
    N = needle.flat()
    N.cast_on(n*2+4)

    for j in range(k):
        for i in range(m):
            N.purl(n)
            N.knit(4)
            N.purl(n)
            N.turn()

            N.knit(n)
            N.purl(4)
            N.knit(n)
            N.turn()

        N.purl(n)
        N.cable(2,2,1,1,1)
        N.purl(n)
        N.turn()

        N.knit(n)
        N.purl(4)
        N.knit(n)
        N.turn()

        for i in range(m):
            N.purl(n)
            N.knit(4)
            N.purl(n)
            N.turn()

            N.knit(n)
            N.purl(4)
            N.knit(n)
            N.turn()

    N.cast_off()
    mesh.relax(5*(n+m))
    display().run()

def circle(n):
    mesh.clear()
    N = needle.circle()
    N.cast_on(6)

    for i in range(n):
        for j in range(6):
            N.knit()
            N.yo()
            N.knit(i)

    N.cast_off()
    mesh.relax(5*n)
    display().run()

def sock(m,n):
    mesh.clear()
    N = needle.tube()
    N.cast_on(6,circum=6*m)

    for i in range(m):
        for j in range(6):
            N.knit()
            N.yo()
            N.knit(i)

    for i in range(n):
        N.knit((m+1)*6)

    N.turn(); N.knit((m+1)*2)
    N.turn(); N.purl((m+1)*2+1)
    N.turn(); N.knit((m+1)*2+2)
    N.turn(); N.purl((m+1)*2+3)

    for i in range(n):
        N.knit((m+1)*6)

    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()

def bobble(n, m):
    w = 2*n + 1
    mesh.clear()
    N = needle.flat()
    N.cast_on(w)
    for i in range(m):
        N.knit(w); N.turn()
        N.purl(w); N.turn()

    N.knit(n)

    N._create_node(1,1,5); N._relax(); N.turn()
    N.purl(5); N.turn()
    N.knit(5); N.turn()
    N.p2tog(); N.purl(1); N.p2tog(); N.turn()
    N.k3tog()

    N.knit(n); N.turn()

    for i in range(m):
        N.purl(w); N.turn()
        N.knit(w); N.turn()

    N.cast_off()
    mesh.relax(10*(n+m))
    display().run()
