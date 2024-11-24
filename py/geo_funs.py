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
def fix_geo_point(geometry):
    if not(str(type(geometry)) == "<class 'shapely.geometry.point.Point'>"):
        geometry = Point(geometry)

    lon, lat = geometry.x, geometry.y
    if not(lon >= 55.5 and lon <=65.2):
        return Point(lat, lon)

    return geometry

def fix_geo_multipoint(multipoint):
    return MultiPoint([fix_geo_point(point) for point in multipoint.geoms])

def fix_lin_ring(lin_ring_coords):
    return [fix_geo_point(single_point) for single_point in lin_ring_coords]


def fix_geo_polygon(polygon):
    new_coords_ext = fix_lin_ring(list(polygon.exterior.coords))
    new_coords_int = [fix_lin_ring(list(interior.coords)) for interior in polygon.interiors]
    return Polygon(new_coords_ext, new_coords_int)

def fix_geo_multipolygon(multipolygon):
    return MultiPolygon([fix_geo_polygon(polygon)
                         for polygon
                         in multipolygon.geoms
                         ]
           )

def fix_geo_obj(geo_obj):
    if geo_obj.geom_type == 'Point':
        return fix_geo_point(geo_obj)

    elif geo_obj.geom_type == 'MultiPoint':
        return fix_geo_multipoint(geo_obj)

    elif geo_obj.geom_type == 'Polygon':
        return fix_geo_polygon(geo_obj)

    elif geo_obj.geom_type == 'MultiPolygon':
        return fix_geo_multipolygon(geo_obj)

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

#returns list with the following elements:
# 0) distances between the point and the closest object
# 1) how many objects are within 500m
# 2) within 500m and 1km
# 3) within 1km and 3km
# 4) within 3km and 5 km
# 5) within 5km and 10 km
# 6) within 10km and 15 km

#if get_area_features = True:
#returns areas of objects following the same principle as above (in km^2)
def get_geo_features(point,
                     geo_obj_series,
                     key,
                     get_area_features = False
    ):
    distances = geo_obj_series.apply(lambda x: closest_dist_geo_obj(point, x)/1000)

    output = [key, min(distances), int((distances < 0.5).sum())]
    for i, dist in enumerate([1, 3, 5, 10, 15], len(output)):
        output.append(int((distances < dist).sum() - output[i - 1]))

    if get_area_features:
        geo_obj_series = geo_obj_series.to_crs(epsg=32637)
        def get_total_area_within_reach(dist_df, reach):
            return (dist_df[dist_df['distances'] < reach]['areas'].sum())/(10**6)

        dist_df = pd.DataFrame({"distances": distances,
                                "areas": geo_obj_series.apply(lambda x: x.area)
                                }
                  )
        output.append(get_total_area_within_reach(dist_df, 0.5))

        for i, dist in enumerate([1, 3, 5, 10, 15], len(output)):
            output.append((get_total_area_within_reach(dist_df, dist) - output[i - 1]))

    return output

def get_geo_features_df(points_df,
                        points_col,
                        key_col,
                        prefix,
                        geo_obj_series,
                        get_area_features = False
    ):
    columns = [key_col]
    columns.extend(list(map(lambda x: prefix + '_' + x, ['closest_km', 'less500m', '0.5-1km', '1-3km', '3-5km', '5-10km', '10-15km'])))

    if get_area_features:
        columns.extend(list(map(lambda x: prefix + '_' +'area_' + x,
                                ['less500m', '0.5-1km', '1-3km', '3-5km', '5-10km', '10-15km'])))
        geo_obj_series

    features_df = pd.DataFrame(columns = columns)
    for i, single_point in enumerate(points_df[points_col]):
        print(f"prefix {prefix}, processing index {i} out of {points_df.shape[0] - 1}")
        print(f"processing point {single_point}")
        features_list = get_geo_features(single_point,
                                         geo_obj_series,
                                         points_df[key_col][i],
                                         get_area_features
                        )

        print("adding to features_df...")
        features_df = pd.concat([features_df,
                                 pd.DataFrame([features_list],
                                              columns = columns
                                 )],
                                ignore_index = True
                      )
        print(features_df.tail(1))
        print("done")

    print("finished")
    return features_df


#transforms str col from data.mos.ru to the correct format
#string -> dict -> polygon/multipolygon
#example: parse_str_to_polygon(df['geoData'])
from shapely.wkt import loads
def parse_str_to_polygon(input_series):

    if input_series[0][:14] == '{coordinates=[':
        return (input_series
                   .apply(lambda x: x
                                    .replace("=", ":")
                                    .replace("coordinates", "'coordinates'")
                                    .replace("type:", "'type':'")
                                    .replace("}", "'}"))
                   .apply(lambda x: shape(eval(x)))
                )
    else:
        return input_series.apply(lambda x: loads(x))

def create_gdf(df,
               col_to_geometry = 'geoData',
               drop_orig_geo_col = True,
               to_fix_geo_obj = True
    ):
    if to_fix_geo_obj:
        df[col_to_geometry] = df[col_to_geometry].apply(lambda x: fix_geo_obj(x))

    gdf = gpd.GeoDataFrame(df, geometry=df[col_to_geometry])
    gdf.set_crs("epsg:4326", allow_override=True, inplace=True)

    if drop_orig_geo_col:
        gdf = gdf.drop(col_to_geometry, axis = 1)

    return gdf


