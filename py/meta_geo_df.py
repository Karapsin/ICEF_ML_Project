import sys
import os
sys.path.append('py')
from geo_plot_funs import *

df = pd.DataFrame(columns = ['geoData', 'group'])
for file in os.listdir('csv\\objects_coords'):
    print(f"processing {file}")
    mini_df = get_csv('objects_coords', file, cols = ['geoData'])
    mini_df['group'] = file.replace('.csv', '')
    mini_df['geoData'] = parse_str_to_polygon(mini_df['geoData']) #just to standartize the format
    df = pd.concat([df, mini_df])
    print("done")

flats = pd.read_csv('csv\\clean_data.csv')[['coords']]
flats['geoData'] = flats['coords'].apply(lambda x: Point(eval(x)))
flats['group'] = 'flats'
flats = flats.drop(['coords'], axis = 1)
df = pd.concat([df, flats])

(create_gdf(df)
 .rename(columns = {"geometry": "geoData"})
 .to_csv("csv//meta_geo_df.csv", index = False)
 )