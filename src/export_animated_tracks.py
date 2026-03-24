import xarray as xr
import numpy as np
import json

print('here')
ds = xr.open_zarr('output/tracks/plastic_tracks.zarr')
lons = ds['lon'].values
lats = ds['lat'].values
times = ds['time'].values

print(f'Tracks: {lons.shape[0]}, Timesteps: {lons.shape[1]}')


sample_step = 10
time_step = 4


point_features = []
line_features = []

for i in range(0, lons.shape[0], sample_step):
    track_lon = lons[i, :]
    track_lat = lats[i, :]
    track_time = times[i, :]

    valid = ~np.isnan(track_lon)
    if valid.sum() < 2:
        continue

    
    coords = list(zip(
        track_lon[valid].astype(float).tolist(),
        track_lat[valid].astype(float).tolist()
    ))
    line_features.append({
        'type': 'Feature',
        'properties': {'particle_id': int(i)},
        'geometry': {'type': 'LineString', 'coordinates': coords}
    })


    for t in range(0, len(track_lon), time_step):
        if np.isnan(track_lon[t]):
            continue
        
        day = int(t * 6 / 24)
        point_features.append({
            'type': 'Feature',
            'properties': {
                'particle_id': int(i),
                'day': day
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [float(track_lon[t]), float(track_lat[t])]
            }
        })

with open('frontend/particle_tracks.geojson', 'w') as f:
    json.dump({'type': 'FeatureCollection', 'features': line_features}, f)
print(f'Exported {len(line_features)} track lines')


with open('frontend/particle_points.geojson', 'w') as f:
    json.dump({'type': 'FeatureCollection', 'features': point_features}, f)
print(f'Exported {len(point_features)} animated points ({len(point_features)//len(line_features)} per track)')


