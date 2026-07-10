import numpy as np
import pandas as pd
import json
import netCDF4 as nc
import xarray as xr
import matplotlib.pyplot as plt
#from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

file = 'centroids_buildings_filtered.geojson'
d= json.load(open(file))

dfr = pd.json_normalize(d, 'features')

dfr['lat'] = dfr['geometry.coordinates'].str[1]
dfr['long'] = dfr['geometry.coordinates'].str[0]

df = dfr[['properties.id','lat','long','properties.Area','properties.Perimeter','properties.walls_surface','properties.height','properties.layer','geometry.coordinates']]

# Load geo_em
dataset_geo_em = xr.open_dataset('geo_em.d03_smooth42.nc')

# make dataframe with lat long of gridcell
df_xlat_m = dataset_geo_em['XLAT_M'][0].to_dataframe()
df_xlong_m = dataset_geo_em['XLONG_M'][0].to_dataframe()

df_xlat_xlong_m = df_xlat_m.copy()

df_xlat_xlong_m['XLONG_M']=df_xlong_m['XLONG_M'].values

df['south_north'] = 0
df['west_east'] = 0
df['XLAT_M'] = 0
df['XLONG_M'] = 0
df['distance2'] = 0


for i in tqdm(range(df.values.shape[0])):
    # lat long building
    lat_i = df['lat'][i]
    long_i = df['long'][i]
    wr = 0.002

    # define dataframe of the cell of mass points enclosing the building
    df_cell_m_i = df_xlat_xlong_m.loc[(df_xlat_xlong_m['XLAT_M'] > lat_i - wr) & 
           (df_xlat_xlong_m['XLONG_M'] < long_i + wr) & 
           (df_xlat_xlong_m['XLAT_M'] < lat_i + wr) & 
           (df_xlat_xlong_m['XLONG_M'] > long_i - wr)]

    # calculate distance with each of the mass points
    df_cell_m_i['distance2'] = (df_cell_m_i.XLAT_M-lat_i)**2+(df_cell_m_i.XLONG_M-long_i)**2

    # find the closest one
    df_m_i = df_cell_m_i.loc[df_cell_m_i['distance2'] == df_cell_m_i['distance2'].min()]

    # reset to get values
    df_m_i = df_m_i.reset_index()

    # overwrite in dataframe
    for column in df_m_i.columns:
        try:
            df.loc[i,column] = df_m_i[column].values[0]
        except:
            pass

df_to_save = df.loc[df['XLAT_M']!=0]
df_to_save.to_csv('buildings_per_gridcell_d03.csv')
df_to_save.to_json('buildings_per_gridcell_d03.json')
