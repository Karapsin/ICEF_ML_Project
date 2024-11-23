import os
sys.path.append('py')
from geo_funs import *

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 320)

#transforms str col from data.mos.ru to the correct format
#string -> dict -> polygon/multipolygon
#example: parse_str_to_polygon(df['geoData'])
def parse_str_to_polygon(input_series):
    return (input_series
               .apply(lambda x: x
                                .replace("=", ":")
                                .replace("coordinates", "'coordinates'")
                                .replace("type:", "'type':'")
                                .replace("}", "'}"))
               .apply(lambda x: shape(eval(x)))
            )

def create_gdf(df,
               col_to_geometry = 'geoData',
               drop_orig_geo_col = True,
               to_fix_geo_obj = True
    ):
    if to_fix_geo_obj:
        df[col_to_geometry] = df[col_to_geometry].apply(lambda x: fix_geo_obj(x))

    gdf = gpd.GeoDataFrame(df, geometry=df[col_to_geometry])
    gdf.set_crs("epsg:3395", allow_override=True, inplace=True)

    if drop_orig_geo_col:
        gdf = gdf.drop(col_to_geometry, axis = 1)

    return gdf


df = pd.read_csv('csv\\clean_data.csv')
df['geoData'] = df['coords'].apply(lambda x: Point(eval(x)))
df = create_gdf(df)

for file_name in os.listdir('csv//objects_coords'):
    if file_name in ("education_objects.csv"):
        continue

    if file_name.replace(".csv", "") + '_features.csv' in os.listdir('csv//finished_geo_features'):
        continue

    print(f"starting {file_name}")
    geo_df = pd.read_csv(f"csv\\objects_coords\\{file_name}",
                          delimiter = ";" if file_name != 'moscow_stations.csv' else ",",
                          skiprows = [1],
                           usecols = ['geoData']
              )
    geo_df['geoData'] = parse_str_to_polygon(geo_df['geoData']) if file_name != 'moscow_stations.csv' else  geo_df['geoData'].apply(lambda x: Point(eval(x)))
    geo_df = create_gdf(geo_df)

    geo_features = get_geo_features_df(df,
                                       'geometry',
                                       'coords',
                                       file_name.replace(".csv", ""),
                                       geo_df['geometry']
                   )
    geo_features.to_csv(f'''csv//finished_geo_features//{file_name.replace(".csv", "") + '_features.csv'}''', index = False)



geo_df = pd.read_csv(f"csv\\objects_coords\\education_objects.csv",
                          delimiter = ";",
                          skiprows = [1],
                          usecols = ['geoData', 'OrgType']
        ).query("OrgType not in ['прочее', 'организация дополнительного образования']")
geo_df['geoData'] = parse_str_to_polygon(geo_df['geoData'])
geo_df = create_gdf(geo_df)

edu_prefix_list = ['edu_uni', 'edu_prof', 'edu_school']
edu_patterns = ['высш', 'проф', '']
for i in range(len(edu_prefix_list)):
    prefix = edu_prefix_list[i]
    pattern = edu_patterns[i]
    current_geo = geo_df.query("OrgType.str.contains(@pattern)")['geometry']

    if prefix + '_features.csv' in os.listdir('csv//finished_geo_features'):
        continue

    get_geo_features_df(df,
                        'geometry',
                        'coords',
                        prefix,
                        current_geo
    ).to_csv(f'''csv//finished_geo_features//{prefix + '_features.csv'}''', index = False)

# some more features
df['center_dist'] = df['geometry'].apply(lambda x: closest_dist_geo_obj(Point((55.755787, 37.617764)), x)/1000)
df['other_flats_at_this_coords'] = df['coords'].duplicated(keep=False).astype(int)

#adding features to the main df
for file_name in os.listdir('csv//finished_geo_features'):
    print(f"adding {file_name}")
    feature_df = pd.read_csv(f'csv//finished_geo_features//{file_name}')
    df = pd.merge(df, feature_df, on = 'coords', how = 'left').drop_duplicates()

#dropping cols which are not needed for modelling
df = df.drop(['coords', 'geometry'], axis = 1).query("`shops_10-15km` > 0")

(pd.get_dummies(df, columns = ["author_type"], drop_first = True)
 .to_csv("csv//data_for_modelling.csv", index = False)
)