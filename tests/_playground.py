"""
Informal playground while developing.
"""

from constance import *


# Example 1
class Point2D(Struct):
    x: int
    y: int


Vector2D = Point2D[2]

my_vector = Vector2D((-20, 8), (10, 15))

stash = bytes(my_vector)

loaded_vector = Vector2D.load(stash)

assert my_vector == loaded_vector


# Example 2

class Circle(Struct):
    center: Point2D
    radius: double


my_circle = Circle((5, 5), 20)

stash = bytes(my_circle)

loaded_circle = Circle.load(stash)

print(loaded_circle)
assert my_circle == loaded_circle

LazyCircles = LazyArray.of(Circle, 1)
print(LazyCircles)

lazy_circles = LazyCircles([(1, 2), 2])
print(pkt := lazy_circles.build())

print(LazyCircles.load(pkt))
