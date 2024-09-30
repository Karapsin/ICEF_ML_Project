import pandas as pd
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
     )

df = (df
        .assign(coords = df['coords_x'].combine_first(df['coords_y']))
        .drop(columns = ['coords_x', 'coords_y'])
      )


#same coords
(df
  .merge((df
           .groupby(['coords', 'floor'])['coords']
           .count()
           .reset_index(name='count')
           .query("count > 1")
          ),
           on = ['coords', 'floor'],
           how = 'inner'

   )
  .to_csv("csv\\same_coords.csv", index = False)
 )
