import os
import cdsapi

c = cdsapi.Client(
    url='https://cds.climate.copernicus.eu/api',
    key='04aa4da3-61e0-4507-a407-1dbbc803c3eb'
)


import cdsapi


client = cdsapi.Client()
client.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': ['reanalysis'],
        'variable': ['10m_u_component_of_wind', '10m_v_component_of_wind'],
        'year': ['2020', '2021', '2022'],
        'month': [f'{m:02d}' for m in range(1, 13)],
        'day': [f'{d:02d}' for d in range(1, 32)],
        'time': ['00:00', '06:00', '12:00', '18:00'],
        'data_format': 'netcdf',
    },
    'data/era5/era5_wind_2020_2022.nc'
)