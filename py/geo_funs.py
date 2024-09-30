from geopy.geocoders import Nominatim
from dadata import Dadata
import time
def get_coords(adress, query_type = "metro"):
    def coords_token(token):
        dadata = Dadata(token)
        result = dadata.suggest(query_type, query=adress, filters = [{ "city": "Москва" }])
        time.sleep(1)
        return [result[0]['data']['geo_lat'], result[0]['data']['geo_lon']] if len(result)!=0 else None

    try:
        print("trying token 1 ...")
        result = coords_token("d3aac740d869b19b2e9fc91e0e97f1ae0c950452")
        return result
    except:
        print('fail')
        print("trying token 2 ...")
        result = coords_token("579c41243b278f436c14e53b08cfcdf89c23d8c6")
        return result


def get_coords2(adress):
    geolocator = Nominatim(user_agent="Tester")
    location = geolocator.geocode(adress)
    time.sleep(1)
    return [location.latitude, location.longitude] if location is not None else None