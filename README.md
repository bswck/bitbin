# Constance

Constance is a Python library for parsing binary data in an object-oriented manner achieved by 
combining the features of [dataclasses](https://docs.python.org/3/library/dataclasses.html) and 
[Construct](https://construct.readthedocs.io/en/latest/index.html) 
(library specialized in declarative parsing and building of binary data).

## Setup
`pip install constance`

## Examples
Constance may be used for stashing your data or sending it through sockets.
Consider following examples:

```py
from bitbin import *


# Create a Struct dataclass that 
# is equivalent to construct.Struct
class Point2D(Struct):
    """Two-dimensional point in the plane."""

    # Declare 2 struct members of type int 
    # (which are by default understood similarly
    # as in C++ - construct.Int32sn)
    x: int
    y: int


# Create an Array type that consists of 2 Structs
# Represented as Array<Point2D, count=2>
Vector2D = Point2D[2]

# Instantiate the 2-dimensional vector by member initializer list
# Other possible methods to do this:
# my_vector = Vector2D(Point2D(-20, 8), Point2D(10, 15))
# my_vector = Vector2D({'x': -20, 'y': 8}, {'x': 10, 'y': 15})
my_vector = Vector2D((-20, 8), (10, 15))

# Transform to bytes. In this case the result is
# b'\xec\xff\xff\xff\x08\x00\x00\x00\n\x00\x00\x00\x0f\x00\x00\x00'
stash = bytes(my_vector)

# Recreate our vector using Struct.load()
# that bases on construct.Struct(...).parse()
loaded_vector = Vector2D.load(stash)

# Check if both are equal
# Equality operator is available thanks to dataclasses
assert my_vector == loaded_vector


# Create a Circle dataclass
# that uses previously created
# Point2D
class Circle(Struct):
    center: Point2D
    radius: double  # construct.Float64n


# Created object repr():
# Circle(center=Point2D(5, 5), radius=20.0)
my_circle = Circle((5, 5), 20)

# b'\x05\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x004@'
stash = bytes(my_circle)

# Circle(center=Point2D(5, 5), radius=20.0)
loaded_circle = Circle.load(stash)

assert my_circle == loaded_circle  # True!
```

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Contact
* [bswck](https://github.com/bswck)

## Similar Projects
* [construct-typing](https://github.com/timrid/construct-typing)
* [construct-classes](https://github.com/matejcik/construct-classes)
