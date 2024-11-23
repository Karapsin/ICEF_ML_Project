import pandas as pd
import numpy as np
df = pd.read_csv("csv\\flats_data_coords.csv")

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 320)

outliers_urls = pd.read_csv("csv\\outliers_to_delete.csv")['url']


df = (df
      .merge(pd.read_csv("csv\\manual_coords.csv"),
             on = "url",
             how = "left"
       )
      .query("url not in(@outliers_urls)")
      .drop_duplicates()
     )


df['coords_x'] = df['coords_x'].apply(lambda x: np.nan if x == '(None, None)' else x)
df = (df
        .assign(coords = df['coords_x'].combine_first(df['coords_y']).combine_first(df['coords_x']))
        .drop(columns = ['coords_x', 'coords_y'])
      )


#same coords processing
df['coord_floor'] = df['coords'] + '_' + df['floor'].astype(str)
df['is_duplicated'] = 0
same_coords_df = (df
                  .merge((df
                           .groupby(['coord_floor'])['coord_floor']
                           .count()
                           .reset_index(name='count')
                           .query("count > 1")
                          ),
                           on = ['coord_floor'],
                           how = 'inner'

                   )
                )
same_coords_df.to_csv("csv\\same_coords.csv", index = False)


same_coords_df = (
  same_coords_df
 .groupby(['coord_floor'])
 .agg(floors_total = ('floors_total', 'mean'),
      rooms = ('rooms', 'mean'),
      meters = ('meters', 'mean'),
      price = ('price', 'mean'),
      author_type = ('author_type', list)
  )
 .reset_index()
 )

same_coords_df['author_type'] = same_coords_df['author_type'].apply(lambda x: 'many_types' if len(set(map(str, x))) > 1 else x[0])
same_coords_df['is_duplicated'] = 1



duplicated_coord_floor = set(same_coords_df['coord_floor'])
final_cols = ['coords', 'price', 'author_type', 'floor', 'floors_total', 'rooms', 'meters', 'is_duplicated']
same_coords_df[['coords', 'floor']] = same_coords_df['coord_floor'].str.split('_', expand = True)

pd.concat([
            (df
             .query("coord_floor not in @duplicated_coord_floor")
             [final_cols]
            ),
            same_coords_df[final_cols]
          ],
          ignore_index = True
).to_csv("csv\\clean_data.csv", index = False)