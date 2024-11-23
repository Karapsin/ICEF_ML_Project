import pandas as pd
import cianparser
sys.path.append('py')
from geo_funs import *

def try_new_query(coords, query):
    if coords is None:
        new_query = f"{query} {station[0]}"
        print(f"fail, trying {new_query}")
        coords = get_coords2(new_query)

    return coords

moscow_stations = cianparser.list_metro_stations()['Московский']
stations_df = pd.DataFrame(columns = ['station', 'coords'])
for station in moscow_stations:

    print(f"searching coords for {station[0]}")
    coords = get_coords(station[0])

    query_list = ["Москва, метро", "Москва, станция",
                  "Москва, железнодорожная станция",
                  "Москва, МЦД"
                  ]

    for query in query_list:
        coords = try_new_query(coords, query)

    if coords is None:
        raise ValueError(f'can not find coords for {station[0]}')

    print('coords found')
    stations_df.loc[len(stations_df)] = [station[0], coords]

stations_df.to_csv('csv\\moscow_stations_coords.csv', index=False)