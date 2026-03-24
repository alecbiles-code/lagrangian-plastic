from parcels import FieldSet, ParticleSet, JITParticle, AdvectionRK4, Field, StatusCode
import xarray as xr
import numpy as np
from datetime import timedelta

# 
# Load GLORYS12 ocean currents and build fireldset
# 
ds = xr.open_zarr('data/glorys_surface.zarr')

ds = ds.sel(
    latitude=slice(-20, 50),
    longitude=slice(-100, 130),
    time=slice('2020-01-01', '2021-04-30')
)
ds = ds.compute()

print(f'GLORYS loaded: {ds.nbytes / 1e9:.1f} GB')

variables = {'U': 'uo', 'V': 'vo'}
dimensions = {'lat': 'latitude', 'lon': 'longitude', 'time': 'time'}

fieldset = FieldSet.from_xarray_dataset(
    ds, variables, dimensions, mesh='spherical'
)
print('FieldSet created successfully!')

# 
# Load ERA5 wind data and add to FieldSet
# 
ds_wind = xr.open_dataset('data/era5/era5_wind_2020_2022.nc', chunks='auto')

ds_wind = ds_wind.sel(
    latitude=slice(50, -20),
    longitude=slice(0, 200),
)

ds_wind = ds_wind.resample(valid_time='1D').mean()
ds_wind = ds_wind.sortby('latitude')


ds_wind = ds_wind.assign_coords(
    longitude=((ds_wind.longitude + 180) % 360) - 180
).sortby('longitude')

ds_wind = ds_wind.compute()

print(f'Wind data shape: {ds_wind["u10"].shape}')
print(f'Wind size: {ds_wind.nbytes / 1e9:.1f} GB')

fieldset.add_field(
    Field('Uwind', ds_wind['u10'].values, lon=ds_wind.longitude.values,
          lat=ds_wind.latitude.values, time=ds_wind.valid_time.values)
)
fieldset.add_field(
    Field('Vwind', ds_wind['v10'].values, lon=ds_wind.longitude.values,
          lat=ds_wind.latitude.values, time=ds_wind.valid_time.values)
)

del ds, ds_wind
print('Wind fields added!')

# 
# kernels
# 
def windage_kernel(particle, fieldset, time):
    """Apply 2% of 10m wind speed to particle velocity (Yoon et al. 2010)."""
    u_wind = fieldset.Uwind[time, particle.depth, particle.lat, particle.lon]
    v_wind = fieldset.Vwind[time, particle.depth, particle.lat, particle.lon]
    lat_rad = particle.lat * 3.14159265358979 / 180.0
    particle_dlon += 0.02 * u_wind * particle.dt / (111320.0 * math.cos(lat_rad))
    particle_dlat += 0.02 * v_wind * particle.dt / 110540.0
def delete_oob_particle(particle, fieldset, time):
    """Delete particles that leave the data domain."""
    if particle.state == StatusCode.ErrorOutOfBounds:
        particle.delete()

# Seed particles at drifter starting positions(from validate_drifters.py output)
# 
drifter_lons = [-29.710, -28.121, 61.685, -42.231, -31.990,
                66.940, -34.474, -39.763, -30.168, -59.440]
drifter_lats = [28.215, 27.490, -14.882, 30.879, 35.288,
                22.504, 33.536, 30.796, 33.766, 30.444]
drifter_times = [np.datetime64('2020-01-01')] * 10

print(f'Seeding {len(drifter_lons)} validation particles')

pset = ParticleSet.from_list(
    fieldset=fieldset,
    pclass=JITParticle,
    lon=drifter_lons,
    lat=drifter_lats,
    time=drifter_times
)

output = pset.ParticleFile('output/tracks/validation_tracks.zarr', outputdt=timedelta(hours=6))

pset.execute(
    [AdvectionRK4, windage_kernel, delete_oob_particle],
    runtime=timedelta(days=90),
    dt=timedelta(hours=1),
    output_file=output,
)

print('val simulation complete!!!!!!!!!!!!!!')