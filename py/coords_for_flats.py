import pandas as pd
sys.path.append('py')
from geo_funs import *

df = pd.read_csv('csv\\consolidated_data.csv')
addresses_df = (df[['url', 'street', 'house_number']]
                 .assign(address = lambda x: "Москва, "+x['street'].str.strip()+', '+x['house_number'].str.strip())
           )

#e.g. "7с3" -> "7 строение 3"
#only specific format is accepted "a1, a2, a3" (i.e. ", " as separator)
#may also be used for "7к3" -> "7 корпус 3", but it seems that dadata understands "к" fine
def change_address(address, house_number_index, letter, replacement):

    def has_numbers(inputString):
        return any(char.isdigit() for char in inputString)

    output = None
    splitted = address.split(",")
    house_number_str = splitted[house_number_index]

    pos = house_number_str.find(letter)

    if pos!=-1:
        before = house_number_str[:pos].strip()
        after = house_number_str[(pos+1):].strip().replace('лит', '')
        if has_numbers(before) and has_numbers(after):
            splitted[house_number_index] = f"{before} {replacement} {after}"
            output = ", ".join(splitted)

    return output

def try_new_address(old_address, coords, letter, replacement):
    if coords is None:
        new_address = change_address(old_address, 2, letter, replacement)
        if new_address is not None:
            print(f"fail, trying {new_address}")
            coords = get_coords(new_address, "address")

    return coords

coords_list = [0]*len(addresses_df)
for i in range(len(addresses_df)):
    address = addresses_df['address'][i]
    print(f"searching coords for {address}")

    coords = get_coords(address, "address")
    options_list = [('с', 'строение'), ('С', 'строение'), ('ск', 'к'), ('к', 'корпус')]

    for letter, replacement in options_list:
        coords = try_new_address(address, coords, letter, replacement)

    if coords is None:
        coords = get_coords2(address)

    coords_list[i] = tuple(coords)

addresses_df['coords'] = coords_list

(df
 .drop_duplicates()
 .merge(addresses_df.drop(columns = ['address', 'street', 'house_number']),
         on = ['url'],
         how = 'left'
  )
 .drop_duplicates()
 .to_csv("csv\\flats_data_coords.csv", index = False)
 )
