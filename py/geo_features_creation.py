import os
import sys
sys.path.append('py')
from features_funs import *

#Part I: csv breaking
dict_edu = {"csv_name": "eco.csv",
            "group_col": 'obj_type',
            "prefix_list": ['edu_uni', 'edu_prof', 'edu_kids', "edu_school"],
            "patterns": ['factory', 'thermal', 'boiler', "waste", "dump"]
            }

dict_eco = {"csv_name": "education_objects.csv",
            "group_col": 'OrgType',
            "prefix_list": ['eco_factory', 'eco_thermal', 'eco_boiler', "eco_dump"],
            "patterns": ['высш', 'проф', 'дошколь', "общеобразователь"]
            }


for single_dict in [dict_edu, dict_eco]:
    break_csv(**single_dict)

#Part II: mass feature creation
df = pd.read_csv('csv\\clean_data.csv')
df['geoData'] = df['coords'].apply(lambda x: Point(eval(x)))
df = create_gdf(df)

#it is much easier to iterate over coordinates,
#and then join features to the main df
points_df = df[['geometry', 'coords']].drop_duplicates().reset_index()

from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers = 4) as executor:
    list(executor
         .map(lambda x: process_coords_file(x, points_df),
              os.listdir("csv//objects_coords")
          )
    )


#Part III: features based on flat coords
if 'other_flats_features.csv' not in os.listdir('csv//finished_geo_features'):
    get_geo_features_df(points_df,
                        'geometry',
                        'coords',
                        'other_flats',
                        points_df['geometry']
    ).to_csv('csv//finished_geo_features//other_flats_features.csv', index = False)

#Part IV: some more features
df['center_dist'] = df['geometry'].apply(lambda x: closest_dist_geo_obj(Point((55.755787, 37.617764)), x)/1000)
df['other_flats_at_this_coords'] = df['coords'].duplicated(keep=False).astype(int)

#adding features to the main df
for file_name in os.listdir('csv//finished_geo_features'):
    print(f"adding {file_name}")
    feature_df = pd.read_csv(f'csv//finished_geo_features//{file_name}')
    df = pd.merge(df, feature_df, on = 'coords', how = 'left').drop_duplicates()

#dropping cols which are not needed for the modelling process
#cleaning from coords for which we can not find proper geo features
df = df.drop(['coords', 'geometry'], axis = 1).query("`shops_10-15km` > 0")

(pd.get_dummies(df, columns = ["author_type"], drop_first = True)
 .to_csv("csv//data_for_modelling.csv", index = False)
)