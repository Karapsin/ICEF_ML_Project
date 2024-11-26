import os
import sys

import pandas as pd

sys.path.append('py')
from features_funs import *

#Part I: csv breaking
dict_edu = {"csv_name": "education_objects.csv",
            "group_col": 'OrgType',
            "prefix_list": ['edu_prof', 'edu_kids', "edu_school"],
            "patterns": ['проф', 'дошколь', "общеобразователь"]
            }

dict_eco = {"csv_name": "eco.csv",
            "group_col": 'obj_type',
            "prefix_list": ['eco_factory', 'eco_thermal', 'eco_boiler', "eco_waste", "eco_dump"],
            "patterns": ['factory', 'thermal', 'boiler', "waste", "dump"]
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


#Part III: some more features
df['center_dist'] = df['geometry'].apply(lambda x: closest_dist_geo_obj(Point((55.755787, 37.617764)), x)/1000)
df['other_flats_at_this_coords'] = df['coords'].duplicated(keep=False).astype(int)

if 'report_sample.csv' not in os.listdir('csv//other_flats_features'):
    (get_geo_features_df(points_df,
                                           'geometry',
                                           'coords',
                                           'other_flats',
                                            points_df['geometry']
                       )
     .to_csv("csv//other_flats_features//report_sample.csv",
             index = False
      )
     )



#adding features to the main df
for file_name in os.listdir('csv//finished_geo_features'):
    print(f"adding {file_name}")
    feature_df = pd.read_csv(f'csv//finished_geo_features//{file_name}')
    df = pd.merge(df, feature_df, on = 'coords', how = 'left').drop_duplicates()

#we can conclude that for such flats we can not derive proper geo features
df = df.query("`shops_10-15km` > 0")

# turns out that some objects are not clustered,
# so there is no point of knowing how many of them are within 500m, ...,
# closest distance feature is enough for them
# (I realized that after looking on map plots)
df = (df
     .drop(['adult_hospitals_less500m',	'adult_hospitals_0.5-1km',	'adult_hospitals_1-3km',
            'adult_hospitals_3-5km', 'adult_hospitals_5-10km', 'adult_hospitals_10-15km',

            'kids_hospitals_less500m',	'kids_hospitals_0.5-1km', 'kids_hospitals_1-3km',
            'kids_hospitals_3-5km', 'kids_hospitals_5-10km', 'kids_hospitals_10-15km',

            'train_stations_less500m',	'train_stations_0.5-1km', 'train_stations_1-3km',
            'train_stations_3-5km',	'train_stations_5-10km', 'train_stations_10-15km',

            'bus_stations_less500m', 'bus_stations_0.5-1km', 'bus_stations_1-3km',
            'bus_stations_3-5km', 'bus_stations_5-10km', 'bus_stations_10-15km',

            'eco_boiler_less500m', 'eco_boiler_0.5-1km', 'eco_boiler_1-3km',
            'eco_boiler_3-5km',	'eco_boiler_5-10km', 'eco_boiler_10-15km',

            'eco_dump_less500m', 'eco_dump_0.5-1km',	'eco_dump_1-3km',
            'eco_dump_3-5km', 'eco_dump_5-10km',	'eco_dump_10-15km',

            'eco_factory_less500m',	'eco_factory_0.5-1km',	'eco_factory_1-3km',
            'eco_factory_3-5km', 'eco_factory_5-10km',	'eco_factory_10-15km',

            'eco_thermal_less500m',	'eco_thermal_0.5-1km',	'eco_thermal_1-3km',
            'eco_thermal_3-5km', 'eco_thermal_5-10km',	'eco_thermal_10-15km',

            'eco_waste_less500m', 'eco_waste_0.5-1km', 'eco_waste_1-3km',
            'eco_waste_3-5km', 'eco_waste_5-10km', 'eco_waste_10-15km',
            
            'edu_prof_less500m', 'edu_prof_0.5-1km',
            'edu_school_less500m',	'edu_school_0.5-1km'
           ],
           axis = 1
      )
     )

#if for duplicated ads we have a room of 3.6, then we conclude that we have 4 rooms
# +0.01 to do math rounding
df['rooms'] = df['rooms'].apply(lambda x: round(x + 0.01))

#some more features
df['other_flats_at_this_coords'] = df['other_flats_at_this_coords'].astype(bool)
df['is_duplicated'] = df['is_duplicated'].astype(bool)

def move_to_end(col):
    b = df.pop(col)
    df.insert(len(df.columns), col, b)

move_to_end('is_duplicated')
move_to_end('other_flats_at_this_coords')
df = df[df['price'] <= df['price'].quantile(0.95)]
df = pd.get_dummies(df, columns = ["author_type", 'rooms'], drop_first = False)

# I realized that 5-10 km or 10-15 is an overkill
df = df.drop(list(filter(lambda x: '5-10km' in x or '10-15km' in x, df.columns)), axis = 1)
df.to_csv("csv//data_for_report.csv")

other_flats_cols = ['coords',
                    'other_flats_closest_km',
                    'other_flats_less500m',
                    'other_flats_0.5-1km',
                    'other_flats_1-3km',
                    'other_flats_3-5km'
                   ]


(df
 .merge(pd.read_csv("csv//other_flats_features//report_sample.csv", usecols = other_flats_cols),
         on = 'coords',
         how = 'left'
  )
 .drop(['coords', 'geometry'], axis = 1)
 .drop_duplicates()
 .to_csv("csv//data_for_report.csv", index = False)
 )

#holdout and model_df
holdout = df.sample(n = 1000, random_state = 228)
df_remaining = df.drop(holdout.index)







df_remaining.to_csv("csv//data_for_modelling.csv", index = False)
holdout.to_csv("csv//holdout.csv", index = False)



