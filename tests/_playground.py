"""
Informal playground while developing.
"""

from constance import *


class Point2D(Struct):
    x: int
    y: int


Vector2D = Point2D[2]

vector_sent = Vector2D((-20, 8), (10, 15))

packet = bytes(vector_sent)

vector_received = Vector2D.load(packet)

assert vector_sent == vector_received
