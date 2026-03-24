import xarray as xr
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2


ds = xr.open_dataset('data/drifters/drifter_6hour_qc_074e_1ebf_81a9_U1773107254430.nc')
drifters = ds.to_dataframe().reset_index()
# netcdf 
# ds = xr.open_dataset('data/drifters/drifter_6hour_qc.nc')
# drifters = ds.to_dataframe().reset_index()

print(f'Total drifter records: {len(drifters):,}')
print(f'Columns: {list(drifters.columns)}')


drifters['time'] = pd.to_datetime(drifters['time'])

mask = (
    (drifters['time'] >= '2020-01-01') &
    (drifters['time'] <= '2020-04-30') &
    (drifters['latitude'] >= -20) & (drifters['latitude'] <= 50) &
    (drifters['longitude'] >= -100) & (drifters['longitude'] <= 130)
)
filtered = drifters[mask].copy()

drifter_starts = filtered.groupby('ID')['time'].min().reset_index()
drifter_starts = drifter_starts[drifter_starts['time'] < '2020-02-01']


drifter_ids = filtered[filtered['ID'].isin(drifter_starts['ID'])]\
    .groupby('ID').size().nlargest(10).index.tolist()

print(f'Selected {len(drifter_ids)} drifters for validation')


validation_drifters = filtered[filtered['ID'].isin(drifter_ids)].copy()

starts = validation_drifters.groupby('ID').first().reset_index()
print('\nDrifter starting positions:')
print(starts[['ID', 'longitude', 'latitude', 'time']])