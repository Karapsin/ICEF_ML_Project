import pandas as pd
from geopy.geocoders import Nominatim
from dadata import Dadata
import time

import geopandas as gpd
from shapely.geometry import shape, Point, Polygon, MultiPolygon, MultiPoint

def get_coords(adress, query_type = "metro"):
    def coords_token(token):
        dadata = Dadata(token)
        result = dadata.suggest(query_type, query=adress, filters = [{ "city": "Москва" }])
        time.sleep(1)
        return [result[0]['data']['geo_lat'], result[0]['data']['geo_lon']] if len(result)!=0 else None

    try:
        print("trying token 1 ...")
        result = coords_token("d3aac740d869b19b2e9fc91e0e97f1ae0c950452")
        return result
    except:
        print('fail')
        print("trying token 2 ...")
        result = coords_token("579c41243b278f436c14e53b08cfcdf89c23d8c6")
        return result


def get_coords2(adress):
    geolocator = Nominatim(user_agent="Tester")
    location = geolocator.geocode(adress)
    time.sleep(1)
    return [location.latitude, location.longitude] if location is not None else None


#those fix funs are used to fix cases when lon and lat are switched
def fix_geo_point(geometry, reverse = False):
    if not(str(type(geometry)) == "<class 'shapely.geometry.point.Point'>"):
        geometry = Point(geometry)

    lon, lat = geometry.x, geometry.y
    if not(reverse):
        if not(lon >= 50 and lon <=65.2):
            return Point(lat, lon)
    else:
            return Point(lat, lon)

    return geometry

def fix_geo_multipoint(multipoint, reverse = False):
    return MultiPoint([fix_geo_point(point, reverse) for point in multipoint.geoms])

def fix_lin_ring(lin_ring_coords, reverse = False):
    return [fix_geo_point(single_point, reverse) for single_point in lin_ring_coords]


def fix_geo_polygon(polygon, reverse = False):
    new_coords_ext = fix_lin_ring(list(polygon.exterior.coords), reverse)
    new_coords_int = [fix_lin_ring(list(interior.coords), reverse) for interior in polygon.interiors]
    return Polygon(new_coords_ext, new_coords_int)

def fix_geo_multipolygon(multipolygon, reverse = False):
    return MultiPolygon([fix_geo_polygon(polygon, reverse)
                         for polygon
                         in multipolygon.geoms
                         ]
           )

def fix_geo_obj(geo_obj, reverse = False):
    if geo_obj.geom_type == 'Point':
        return fix_geo_point(geo_obj, reverse)

    elif geo_obj.geom_type == 'MultiPoint':
        return fix_geo_multipoint(geo_obj, reverse)

    elif geo_obj.geom_type == 'Polygon':
        return fix_geo_polygon(geo_obj, reverse)

    elif geo_obj.geom_type == 'MultiPolygon':
        return fix_geo_multipolygon(geo_obj, reverse)

    else:
        raise ValueError("Unknown geo object")

#following dist funs are used to compute closest geodesic distance
#between given point and Point, Polygon or Multipolygon
from geopy.distance import geodesic
# distance between 2 points (in meters)
def dist_points(point1, point2):
    return geodesic(point1, point2).meters if isinstance(point1, tuple) else geodesic((point1.x, point1.y), (point2.x, point2.y)).meters

def dist_multipoint(point, multipoint, min_start = float('inf')):
    min_distance = min_start
    for single_point in multipoint.geoms:
        current_dist = dist_points(point, single_point)
        min_distance = min(min_distance, current_dist)

    return min_distance

# returns closest distances between a point and a polygon (in meters)
def closest_dist_polygon(point, polygon, min_start=float('inf')):
    min_distance = min_start
    for coord in list(polygon.exterior.coords):
        current_dist = dist_points(coord, point.coords[0])
        min_distance = min(min_distance, current_dist)

    for interior in polygon.interiors:
        for coord in interior.coords:
            current_dist = dist_points(coord, point.coords[0])
            min_distance = min(min_distance, current_dist)

    return min_distance


def closest_dist_multipolygon(point, multipolygon, min_start=float('inf')):
    min_distance = min_start
    for polygon in multipolygon.geoms:
        min_distance = min(min_start, closest_dist_polygon(point, polygon, min_distance))

    return min_distance


def closest_dist_geo_obj(point, geo_obj):
    if geo_obj.geom_type == 'Point':
        return dist_points(point, geo_obj)
    elif geo_obj.geom_type == 'MultiPoint':
        return dist_multipoint(point, geo_obj)
    elif geo_obj.geom_type == 'Polygon':
        return closest_dist_polygon(point, geo_obj)
    elif geo_obj.geom_type == 'MultiPolygon':
        return closest_dist_multipolygon(point, geo_obj)
    else:
        raise ValueError("Unknown geo object")

