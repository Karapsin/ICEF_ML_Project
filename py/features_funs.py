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

#quite messy, sorry
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