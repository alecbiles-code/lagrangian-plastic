import xarray as xr

# Open all GLglorysORYS files LAZILYY with Dask
ds = xr.open_mfdataset(
    'data/glorys/*.nc',
    chunks={'time': 30, 'latitude': 100, 'longitude': 100},
    parallel=True
)

# size before converting please no more crashes
print(ds)
print(f'Total size: {ds.nbytes / 1e9:.1f} GB')

# zarrrrrrr
ds.to_zarr('data/glorys_surface.zarr', consolidated=True, mode='w')
print('Zarr conversion complete!')
