#this json been stolen from this site:
#https://mwmoskva.ru/ekologicheskaya-karta-moskvy.html
#json link:
#https://mwmoskva.ru/js/datamos/eco.json

from bs4 import BeautifulSoup
import pandas as pd
import json
sys.path.append('py')
from geo_funs import *
with open('json//eco.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 0 - coords
# 1 - letter ???
# 2 - descr
# 3 - num ???
# 4 - num2 ???
parsed_json = {"coords": [], "descr": []}
for single_list in data:
    parsed_json["coords"].append(single_list[0])
    parsed_json["descr"].append(single_list[2])

df = pd.DataFrame(parsed_json)
df['descr'] = df['descr'].apply(lambda x: BeautifulSoup(x, "html.parser").get_text())

#save to check manually
df.to_excel("xlsx//eco_manual_clean.xlsx", index = False)

#further cleaning
df = (pd.read_excel("xlsx//eco_manual_cleaned.xlsx")
      .query("not(descr.str.contains('ерпух') or descr.str.contains('лектростал'))")
     )

def parse_polygon(x):
    return Polygon([(x[i], x[i + 1]) for i in range(0, len(x), 2)])

df['geoData'] = (df['coords']
                 .apply(lambda x: eval(x))
                 .apply(lambda x: Point(x) if len(x) == 2 else parse_polygon(x))
                 .apply(lambda x: str(x))
                )
df['descr'] = df['descr'].str.lower()


import numpy as np
import re
def check_series(patterns):
    def check_patterns(x, patterns):
        return any(re.search(pattern, x) for pattern in patterns)
    return df['descr'].apply(lambda x: check_patterns(x, patterns))


df['obj_type'] = np.where(check_series(["полигон тбо"]), "dump",
                 np.where(check_series(["мусор", "очистн"]), "waste",
                 np.where(check_series(["теплов", "тэц", "тэс меж", "гтэс", "грэс"]), "thermal",
                 np.where(check_series(["котельн"]), "boiler", "factory"
                 ))))

from shapely.wkt import loads
df['centr_dist'] = df['geoData'].apply(lambda x: loads(x)).apply(lambda x: closest_dist_geo_obj(Point((55.755787, 37.617764)), x)/1000)
df = df.query("centr_dist < 50")


df.to_csv("csv//csv_to_split//eco.csv", index = False)
df.to_excel("xlsx//eco.xlsx", index = False)