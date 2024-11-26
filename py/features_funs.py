import sys
import os
sys.path.append('py')
from geo_funs import *

import chardet
import csv
def get_delimiter(file_path, n = 15000):

    with open(file_path, 'rb') as file:
        encoding = chardet.detect(file.read())['encoding']

    with open(file_path,  'r', encoding = encoding) as file:
        sample = file.read(n)
        detected_delimiter = csv.Sniffer().sniff(sample).delimiter

    return detected_delimiter

def get_rows_to_skip(delimiter):
    return [1] if delimiter == ';' else None

def get_csv(folder, file_name, cols = ['geoData']):
    file_path = f"csv\\{folder}\\{file_name}"
    delimiter = get_delimiter(file_path)
    return pd.read_csv(file_path,
                       delimiter = delimiter,
                       skiprows = get_rows_to_skip(delimiter),
                       usecols = cols
            )


def break_csv(csv_name, group_col, prefix_list, patterns):
    for i in range(len(prefix_list)):

        #not reliable data :(
        if prefix_list[i] == "edu_kids":
            continue

        if prefix_list[i] + '.csv' in os.listdir('csv//objects_coords'):
            continue
        pattern = patterns[i]
        (get_csv("csv_to_split", f"{csv_name}", ['geoData', group_col])
         .query(f"{group_col}.str.contains(@pattern)")
         .to_csv(f'''csv//objects_coords//{prefix_list[i]}.csv''', index=False)
         )


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


from shapely.wkt import loads
def process_coords_file(file_name, points_df):
    if file_name.replace(".csv", "") + '_features.csv' in os.listdir('csv//finished_geo_features'):
        return f'skipping {file_name}'

    print(f"starting {file_name}")
    geo_df = get_csv("objects_coords", f"{file_name}", ['geoData'])
    geo_df['geoData'] = parse_str_to_polygon(geo_df['geoData'])
    geo_df = create_gdf(geo_df)

    geo_features = get_geo_features_df(points_df,
                                       'geometry',
                                       'coords',
                                       file_name.replace(".csv", ""),
                                       geo_df['geometry'],
                                       False if file_name != "parks.csv" else True
                   )
    geo_features.to_csv(f'''csv//finished_geo_features//{file_name.replace(".csv", "") + '_features.csv'}''', index = False)

    return f'finished {file_name}'