import pandas as pd, numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_regression, RFE
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import re 

pd.set_option('display.float_format', '{:.4f}'.format)

def get_x_y(csv_name):
    df = pd.read_csv(f'csv\\{csv_name}.csv')
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