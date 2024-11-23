#semi-manual
import cianparser
import pandas as pd
import os

os.chdir("data_load")
already_parsed_set = set([x.split('.csv', 1)[0] for x in os.listdir()])
for subway_list in cianparser.list_metro_stations()['Московский']:
    for room_num in range(1, 4):
        if f'Moscow_{subway_list[0]}_{str(room_num)}' not in already_parsed_set:
            print(f"parsing {subway_list[0]}, room number: {str(room_num)}")
            moscow_parser = cianparser.CianParser(location="Москва")
            data = moscow_parser.get_flats(deal_type="rent_long",
                                           rooms = (room_num),
                                           with_saving_csv=False,
                                           with_extra_data = False,
                                           additional_settings={"start_page":1,
                                                                "end_page":2,
                                                                "only_flat ":True,
                                                                "sort_by": "creation_data_from_newer_to_older",
                                                                "metro": 'Московский',
                                                                "metro_station": subway_list[0]
                                                                }
                                   )
            pd.DataFrame(data).to_csv(f'Moscow_{subway_list[0]}_{str(room_num)}.csv')

        else:
            print(f"skipping {subway_list[0]}, room number: {str(room_num)}")

