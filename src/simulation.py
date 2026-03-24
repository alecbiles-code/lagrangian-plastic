from parcels import FieldSet, ParticleSet, JITParticle, AdvectionRK4, Field, StatusCode
import xarray as xr
import numpy as np
from datetime import timedelta

# 
# Load GLORYS12 ocean currents and build FieldSet
# Subset to roi to save memory
# 
ds = xr.open_zarr('data/glorys_surface.zarr')

ds = ds.sel(
    latitude=slice(-20, 50),
    longitude=slice(-100, 130),
    time=slice('2020-01-01', '2021-04-30')
)
ds = ds.compute()
print(ds)
print(f'GLORYS loaded: {ds.nbytes / 1e9:.1f} GB')

variables = {'U': 'uo', 'V': 'vo'}
dimensions = {'lat': 'latitude', 'lon': 'longitude', 'time': 'time'}

fieldset = FieldSet.from_xarray_dataset(
    ds, variables, dimensions, mesh='spherical'
)
print('FieldSet created successfully!')

# Load ERA5 wind data and add to FieldSet
#         Subset to same region to save memory
# 
ds_wind = xr.open_dataset('data/era5/era5_wind_2020_2022.nc', chunks='auto')

ds_wind = ds_wind.sel(
    latitude=slice(50, -20),
    longitude=slice(0, 200),
)

ds_wind = ds_wind.resample(valid_time='1D').mean()
ds_wind = ds_wind.sortby('latitude')

# Convert ERA5 longitude from 0-360 to -180 to 180 to match GLORYS
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

# Free the xarray objects now that data is in the FieldSet
del ds, ds_wind
print('Wind fields added! (source arrays freed from memory)')

# 
#Define windage kernel (2% wind-driven drift)
# 
def windage_kernel(particle, fieldset, time):
    """Apply 2% of 10m wind speed to particle velocity (Yoon et al. 2010)."""
    u_wind = fieldset.Uwind[time, particle.depth, particle.lat, particle.lon]
    v_wind = fieldset.Vwind[time, particle.depth, particle.lat, particle.lon]
    # Convert displacement from meters to degrees
    lat_rad = particle.lat * math.pi / 180.0
    particle_dlon += 0.02 * u_wind * particle.dt / (111320.0 * math.cos(lat_rad))
    particle_dlat += 0.02 * v_wind * particle.dt / 110540.0

# Define kernel to handle out-of-bounds particles
# 
def delete_oob_particle(particle, fieldset, time):
    """Delete particles that leave the data domain."""
    if particle.state == StatusCode.ErrorOutOfBounds:
        particle.delete()

# Define particle seeding locationsT
# 
sources = {
    # Asia rivers(
    'Yangtze':      (121.9, 31.4),
    'Ganges':       (89.0, 22.0),
    'Xi':           (113.3, 22.1),
    'Huangpu':      (121.5, 31.2),
    'Mekong':       (106.6, 10.0),
    'Indus':        (67.3, 23.9),
    'Brantas':      (112.7, -7.5),
    'Solo':         (112.5, -6.9),
    'Serayu':       (109.3, -7.7),
    'Pasig':        (120.9, 14.5),
    'Irrawaddy':    (95.2, 16.4),
    'Zhujiang':     (113.6, 22.2),

    # Africa
    'Cross':        (8.3, 4.6),
    'Imo':          (7.3, 4.5),
    'Kwa_Ibo':      (7.9, 4.5),

    # South America
    'Amazon':       (-49.3, -0.5),
    'Magdalena':    (-75.0, 11.0),

    # North America
    'Mississippi':  (-89.4, 29.0),
}

seed_lons, seed_lats, seed_times = [], [], []
base_time = np.datetime64('2020-01-01')

for name, (lon, lat) in sources.items():
    n_particles = 1000
    seed_lons.extend([lon + np.random.normal(0, 0.1) for _ in range(n_particles)])
    seed_lats.extend([lat + np.random.normal(0, 0.1) for _ in range(n_particles)])
    seed_times.extend([base_time + np.timedelta64(np.random.randint(0, 30), 'D')
                       for _ in range(n_particles)])

print(f'Seeding {len(seed_lons)} particles from {len(sources)} rivers')

pset = ParticleSet.from_list(
    fieldset=fieldset,
    pclass=JITParticle,
    lon=seed_lons,
    lat=seed_lats,
    time=seed_times
)

output = pset.ParticleFile('output/tracks/plastic_tracks.zarr', outputdt=timedelta(hours=6))

pset.execute(
    [AdvectionRK4, windage_kernel, delete_oob_particle],
    runtime=timedelta(days=90),   # Start with 90 days; increase to 365 once confirmed working
    dt=timedelta(hours=1),
    output_file=output,
)


print(f'Output saved output/tracks/plastic_tracks.zarr')