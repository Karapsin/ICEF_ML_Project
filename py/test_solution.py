from random import randint
def rnum():
    return randint(1, 100)
x1 = rnum()
x4 = rnum()
x2 = 2*x1-2-(5/8)*x4
x3 = 1 + (17/8)*x4

print(isclose((2*x1 - x2 + 3*x3 - 7*x4), 5))
print(isclose((6*x1 - 3*x2 + x3 -4*x4), 7))
print(isclose((4*x1 - 2*x2 + 14*x3 - 31*x4), 18))

from math import  isclose
from random import randint
def rnum():
    return randint(1, 100)

x2 = rnum()
x4 = rnum()
x1 = 1 + (x2/2) + (5/16)*x4
x3=1+(17/8)*x4

print(isclose((2*x1 - x2 + 3*x3 - 7*x4), 5))
print(isclose((6*x1 - 3*x2 + x3 -4*x4), 7))
print(isclose((4*x1 - 2*x2 + 14*x3 - 31*x4), 18))

def true_sol(x3, x4):
    return (x3+x4, x4-x3, x3, x4)

x3 = rnum()
x4 = rnum()

x1 = true_sol(x3, x4)[0]
x2 = true_sol(x3, x4)[1]

x

(x3-x2, (x3-x4)/2, x3, x4)



x