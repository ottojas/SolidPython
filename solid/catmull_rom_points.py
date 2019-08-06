#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from solid import *
from solid.utils import *
from euclid3 import Vector2, Vector3, Point2, Point3

from typing import Sequence, Tuple, Union

Point23 = Union[Point2, Point3]
Vec23 = Union[Vector2, Vector3]
FourPoints = Tuple[Point23, Point23, Point23, Point23]
SEGMENTS = 48

# Python port of C# code at: https://www.habrador.com/tutorials/interpolation/1-catmull-rom-splines/
# retrieved 20190712

def _catmull_rom_segment(controls: FourPoints, subdivisions: int, include_last=False) -> Sequence[Point23]: 
    pos: Point23 = None
    positions: Sequence[Point23] = []

    num_points = subdivisions
    if include_last:
        num_points += 1

    p0, p1, p2, p3 = controls
    a = 2 * p1
    b = p2 - p0
    c = 2* p0 - 5*p1 + 4*p2 - p3
    d = -p0 + 3*p1 - 3*p2 + p3

    for i in range(num_points):
        t = i/subdivisions
        pos = 0.5 * (a + (b * t) + (c * t * t) + (d * t * t * t))
        positions.append(pos)
    return positions

def catmull_rom_tangents(points: Sequence[Point23],
                        subdivisions: int, 
                        start_tangent: Vec23,
                        end_tangent: Vec23 ) -> Sequence[Point23]:
    # Return an open (non-loop) list of points connecting all points in points.
    # Specify tangent vectors at the start and end of the curve
    cat_points = [points[0]+ start_tangent] + points + [points[-1] + end_tangent]
    return catmull_rom_points(cat_points, subdivisions, close_loop=False)

def catmull_rom_points(points: Sequence[Point23], 
                       subdivisions:int, 
                       close_loop: bool=False)-> Sequence[Point23]:
    # Return a smooth set of points through points. If close_loop is True,
    # all points will be included. If close_loop is False, the first and last points
    # and their associated segments won't be included. 
    # If you want an open curve with all points included, see catmull_rom_tangents()
    catmull_points: Sequence[Point23] = []

    last_point_range = len(points) if close_loop else len(points) - 3

    for i in range(0, last_point_range):
        include_last = True if i == last_point_range - 1 else False
        controls = points[i:i+4]
        # If we're closing a loop, controls needs to wrap around the end of the array
        overflow = i+4 - len(points)
        if overflow > 0:
            controls += points[0:overflow]
        catmull_points += _catmull_rom_segment(controls, subdivisions, include_last)
    # NOTE: if a loop is closed, the interpolated points between point 0 & 1
    # will come *last* in the returned array, when one might expect them to come first.
    # In that case, we might want to insert those subdivisions points

    return catmull_points

def bottle_shape(width: float, height: float, neck_width:float=None, neck_height:float=None):

    if neck_width == None:
        neck_width = width * 0.4
    
    if neck_height == None:
        neck_height = height * 0.2

    w2 = width/2
    nw2 = neck_width/2
    h = height
    nh = neck_height

    corner_rad = 0.5

    guide_in = [Point2(nw2, h + 1)]
    # Add extra tangent points near curves to keep
    # cubics from going crazy. Is there a better way?
    points = [
        Point2(nw2, h),
        Point2(nw2, h-nh + 1),      # <- extra tangent
        Point2(nw2, h - nh),    
        Point2(w2, h-nh-1),         # <- extra tangent
        Point2(w2, corner_rad + 1), # <- extra tangent
        Point2(w2, corner_rad),
        Point2(w2-corner_rad, 0)    # <- extra tangent
    ]
    guide_out = [Point2(0,0)]
    cat_points = guide_in + points + guide_out
    cr_points = catmull_rom_points(cat_points, subdivisions=10, close_loop=False)

    cr_points.insert(0, (0,h))
    cr_points.append((0,0))
    cr_points.append((0,h))
    
    a = polygon(cr_points) 
    a += mirror(v=(1,0))(a)

    cyl = color(Red)(cylinder(r=0.1, h=2, center=True))
    cylinders = [translate(p)(cyl) for p in cat_points]
    a += cylinders
    return a

def bottle_shape_tangents(width: float, height: float, neck_width:float=None, neck_height:float=None):

    if neck_width == None:
        neck_width = width * 0.4
    
    if neck_height == None:
        neck_height = height * 0.2

    w2 = width/2
    nw2 = neck_width/2
    h = height
    nh = neck_height

    corner_rad = 0.5

    start_tangent = Vector2(0, 1)
    end_tangent = Vector2(-1, 0)
    subdivisions = 10
    # Add extra tangent points near curves to keep
    # cubics from going crazy. Is there a better way?
    points = [
        Point2(nw2, h),
        Point2(nw2, h-nh + 1),      # <- extra tangent
        Point2(nw2, h - nh),    
        Point2(w2, h-nh-1),         # <- extra tangent
        Point2(w2, corner_rad + 1), # <- extra tangent
        Point2(w2, corner_rad),
        Point2(w2-corner_rad, 0),
        Point2(0,0),
    ]
    cr_points = catmull_rom_tangents(points, subdivisions, start_tangent, end_tangent)

    cr_points.insert(0, (0,h))
    cr_points.append((0,h))
    
    a = polygon(cr_points) 
    a += mirror(v=(1,0))(a)

    cyl = color(Red)(cylinder(r=0.1, h=2, center=True))
    cylinders = [translate(p)(cyl) for p in points]
    a += cylinders
    return a

def catmull_rom_spline():
    points = [
        Point2(0,0),
        Point2(1,1),
        Point2(2,1),
        Point2(2,-1),
    ]   
    subdivisions=10
    curve_points_open   = catmull_rom_points(points, subdivisions, close_loop=False)
    curve_points_closed = catmull_rom_points(points, subdivisions, close_loop=True)
    
    curve_points_open = [list(p) for p in curve_points_open]
    curve_points_closed = [list(p) for p in curve_points_closed]
    
    a = polygon(curve_points_closed)
    a += right(5)(polygon(curve_points_open))

    return a

if __name__ == '__main__':
    # a = catmull_rom_spline()
    # a = bottle_shape(4, 15)
    a = bottle_shape_tangents(4, 15)
    scad_render_to_file(a, file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)