from numpy import array

zero = array([0,0,0])

X = array([1,0,0])
Y = array([0,1,0])
Z = array([0,0,1])

I = array([X,Y,Z])

rotX = array([  -Z, zero, X])
rotY = array([zero,   -Z, Y])
