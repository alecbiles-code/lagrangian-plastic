import xarray as xr
import numpy as np
import json


ds = xr.open_zarr('output/tracks/plastic_tracks.zarr')
lons = ds['lon'].values
lats = ds['lat'].values

print(f'Tracks: {lons.shape[0]}, Timesteps: {lons.shape[1]}')

sample_step = 10
time_step = 4

features = []
for i in range(0, lons.shape[0], sample_step):
    track_lon = lons[i, ::time_step]
    track_lat = lats[i, ::time_step]
    valid = ~np.isnan(track_lon)

    if valid.sum() < 2:
        continue

    coords = list(zip(
        track_lon[valid].astype(float).tolist(),
        track_lat[valid].astype(float).tolist()
    ))

    features.append({
        'type': 'Feature',
        'properties': {'particle_id': int(i)},
        'geometry': {
            'type': 'LineString',
            'coordinates': coords
        }
    })

geojson = {
    'type': 'FeatureCollection',
    'features': features
}

with open('frontend/particle_tracks.geojson', 'w') as f:
    json.dump(geojson, f)

print(f'Exported {len(features)} tracks to frontend/particle_tracks.geojson')
