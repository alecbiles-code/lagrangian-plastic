import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2

def haversine_km(lon1, lat1, lon2, lat2):
    """Great circle distance between two points in km."""
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

#load sim tracks
sim = xr.open_zarr('output/tracks/validation_tracks.zarr')
print('Simulated tracks:')
print(sim)

print ('here')
ds_drifters = xr.open_dataset('data/drifters/drifter_6hour_qc_074e_1ebf_81a9_U1773107254430.nc')
drifters = ds_drifters.to_dataframe().reset_index()
drifters['time'] = pd.to_datetime(drifters['time'])

# Filter to selected drifter IDs (pasted from Step 2)
selected_ids = [122705, 122706, 132685, 133133, 145694, 147134, '300234062321360', '300234062326350', '300234062329370', '300234062854730'] # REPLACE WITH YOUR IDS
real = drifters[drifters['ID'].isin(selected_ids)].copy()


separations = {}

for i, drifter_id in enumerate(selected_ids):
    real_track = real[real['ID'] == drifter_id].sort_values('time')
    if real_track.empty:
        print(f'Drifter {drifter_id}: no matching data, skipping')
        continue
    

    sim_lon = sim['lon'].values[i, :]
    sim_lat = sim['lat'].values[i, :]
    sim_time = sim['time'].values[i, :]
    

    distances = []
    times = []
    
    for t_idx in range(len(sim_time)):
        t = pd.Timestamp(sim_time[t_idx])
        if pd.isna(t):
            continue
        
        # Find nearest real observation
        #time_diffs = abs(real_track['time'] - t)
        #nearest_idx = time_diffs.idxmin()
        # Find nearest real observation
        time_diffs = abs(real_track['time'] - t)
        if time_diffs.empty:
            continue
        nearest_idx = time_diffs.idxmin()
        
        if time_diffs[nearest_idx] < pd.Timedelta(hours=6):
            r = real_track.loc[nearest_idx]
            d = haversine_km(sim_lon[t_idx], sim_lat[t_idx],
                           r['longitude'], r['latitude'])
            distances.append(d)
            times.append((t - real_track['time'].iloc[0]).days)
    
    separations[drifter_id] = {'times_days': times, 'distance_km': distances}
    mean_sep = np.mean(distances) if distances else float('nan')
    print(f'Drifter {drifter_id}: mean separation = {mean_sep:.1f} km '
          f'({len(distances)} matched points)')


# Separation distance over time

fig, ax = plt.subplots(figsize=(10, 6))

for drifter_id, data in separations.items():
    ax.plot(data['times_days'], data['distance_km'], label=f'Drifter {drifter_id}', alpha=0.7)

ax.axhline(y=100, color='red', linestyle='--', label='100 km target (30-day)')
ax.set_xlabel('Days since release')
ax.set_ylabel('Separation distance (km)')
ax.set_title('Simulated vs. Observed Drifter Separation Distance')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/figures/separation_distance.png', dpi=150)
print('Saved: output/figures/separation_distance.png')


# Plot 2: Simulated vs observed trajectories side by side
#
fig, ax = plt.subplots(figsize=(12, 8))

colors = plt.cm.tab10(np.linspace(0, 1, len(selected_ids)))
print(f'\nDEBUG: real drifter records: {len(real)}')
print(f'DEBUG: selected IDs: {selected_ids}')
print(f'DEBUG: unique IDs in real data: {real["ID"].nunique()}')
print(f'DEBUG: sim lon shape: {sim["lon"].shape}')
print(f'DEBUG: sim lon sample: {sim["lon"].values[0, :5]}')
for i, (drifter_id, color) in enumerate(zip(selected_ids, colors)):
    # Real track
    real_track = real[real['ID'] == drifter_id].sort_values('time')
    if real_track.empty:
        continue
    ax.plot(real_track['longitude'], real_track['latitude'],
            color=color, linewidth=1.5, label=f'Observed {drifter_id}')
    
    # Simulated track
    sim_lon = sim['lon'].values[i, :]
    sim_lat = sim['lat'].values[i, :]
    valid = ~np.isnan(sim_lon)
    ax.plot(sim_lon[valid], sim_lat[valid],
            color=color, linewidth=1.5, linestyle='--', alpha=0.7)
    
    # Mark start
    ax.scatter(real_track['longitude'].iloc[0], real_track['latitude'].iloc[0],
              color=color, s=80, zorder=5, edgecolors='black')

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Simulated (dashed) vs. Observed (solid) Drifter Trajectories')
ax.legend(loc='upper left', fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('output/figures/trajectory_comparison.png', dpi=150)
print('Saved: output/figures/trajectory_comparison.png')

plt.show()