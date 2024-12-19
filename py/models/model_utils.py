from shapely.geometry import Point
import pandas as pd, numpy as np
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_regression, RFE
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import re 
import geopandas as gpd


pd.set_option('display.float_format', '{:.4f}'.format)

def create_gdf(df,
               col_to_geometry = 'geoData',
               drop_orig_geo_col = True,
               to_fix_geo_obj = True
    ):
    if to_fix_geo_obj:
        df[col_to_geometry] = df[col_to_geometry].apply(lambda x: fix_geo_obj(x))

    gdf = gpd.GeoDataFrame(df, geometry=df[col_to_geometry])
    gdf.set_crs("epsg:4326", allow_override=True, inplace=True)

    if drop_orig_geo_col:
        gdf = gdf.drop(col_to_geometry, axis = 1)

    return gdf


def get_x_y(csv_name):
    df = pd.read_csv(f'csv\\{csv_name}.csv')


    df[['latitude', 'longitude']] = (
    df['coords']
    .str.replace("'", "")
    .str.strip()
    .str.strip('()') 
    .str.split(', ', expand=True)  
    .apply(lambda col: col.astype(float)) 
    )

    df['geoData'] = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]

    df = df.drop(['coords', 'longitude', 'latitude'], axis = 1)
    df = create_gdf(df, to_fix_geo_obj = False)

    df = pd.DataFrame(df.to_crs('EPSG:3857'))
    df['geometry'] = df['geometry'].apply(lambda x: [float(s) for s in str(x).replace("POINT", "").strip(" ()").split()])
    df[['latitude', 'longitude']] = df['geometry'].apply(pd.Series)
    df = df.drop(['geometry'], axis = 1)

    X = df.drop(['price', 'other_flats_less500m', 'other_flats_0.5-1km', 'other_flats_1-3km', 'other_flats_3-5km'], axis = 1)
    y = df['price']

    return X, y

def get_cols_with_pattern(df, pattern):
    return df.columns[df.columns.str.contains(pattern)].to_list()

def get_MAE(errors):
    mae = np.mean(np.abs(errors))
    print(f"MAE {mae}")
    return mae

def get_MAPE(errors, y_true):
    mape = np.mean(np.abs(errors)/y_true)
    print(f"MAPE {mape*100}%")
    return mape

from itertools import combinations
def get_combs_list(input_list, upper = None):
    all_combinations = list()
    up_lim = upper + 1 if upper is not None else (len(input_list) + 1)
    for r in range(1, up_lim):
        all_combinations.extend(combinations(input_list, r))
    
    return [list(x) for x in all_combinations]


def get_names_indxs(needed_names_arr, all_names_arr):
    return np.where(np.isin(all_names_arr, needed_names_arr))[0]
