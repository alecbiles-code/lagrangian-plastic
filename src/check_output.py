import xarray as xr
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import h3
import matplotlib.pyplot as plt

#
# load sim output
# 
print('Loading simulation output')
ds = xr.open_zarr('output/tracks/plastic_tracks.zarr')

lons = ds['lon'].values
lats = ds['lat'].values
print(f'data shape: {lons.shape}')

#find each particles last valid (non-nan) position
final_lons = []
final_lats = []

for i in range(lons.shape[0]):
    track_lon = lons[i, :]
    track_lat = lats[i, :]
    valid = ~np.isnan(track_lon)

    if valid.sum() > 0:
        final_lons.append(track_lon[valid][-1])
        final_lats.append(track_lat[valid][-1])

print(f'particles with valid tracks: {len(final_lons)} / {lons.shape[0]}')

#
# Identify beached particles


# Use a  distance-to-coast approach instead of buffering the full coastline (much faster)
#
print('Loading coastline data...')
try:
    coast = gpd.read_file('data/coastlines/gshhg-shp-2.3.7/GSHHS_shp/l/GSHHS_l_L1.shp')
    print(f'coastline loaded: {len(coast)} polygons')
except Exception as e:
    print(f'Error loading coast: {e}')
    raise
print("here")
# Build a GeoDataFrame of final particle positions
print('Building particle GeoDataFrame...')
final_points = gpd.GeoDataFrame(
    {'lon': final_lons, 'lat': final_lats},
    geometry=[Point(lon, lat) for lon, lat in zip(final_lons, final_lats)],
    crs='EPSG:4326'
)
print(f'Final points GeoDataFrame: {len(final_points)} particles')

# use spatial join with buffered coastline

print('Buffering coastline (this may take a minute)...')
try:
    # simplify coastline  to speed up the buffer
    coast_simple = coast.copy()
    coast_simple['geometry'] = coast_simple.geometry.simplify(0.1)
    print(f'Coastline simplified')

    coast_simple['geometry'] = coast_simple.geometry.buffer(0.25)
    print(f'Coastline buffered')

    coast_union = coast_simple.unary_union
    print(f'Coastline union created')
except Exception as e:
    print(f'Error during coastline processing: {e}')
    raise

#particles  inside the buffered coastline
print('Checking beached particles (this may take a few minutes)...')
beached_mask = []
for i, (lon, lat) in enumerate(zip(final_lons, final_lats)):
    if i % 2000 == 0:
        print(f'  Checking particle {i}/{len(final_lons)}...')
    point = Point(lon, lat)
    beached_mask.append(coast_union.contains(point))

beached_lons = [lon for lon, b in zip(final_lons, beached_mask) if b]
beached_lats = [lat for lat, b in zip(final_lats, beached_mask) if b]

print(f'Beached particles: {len(beached_lons)} / {len(final_lons)} '
      f'({100 * len(beached_lons) / len(final_lons):.1f}%)')

# 
#  H3 hexagonal aggregation
# 
print('aggregating into H3 hexagons...')

hex_counts = {}
for lon, lat in zip(beached_lons, beached_lats):
    h = h3.latlng_to_cell(lat, lon, 5)
    hex_counts[h] = hex_counts.get(h, 0) + 1

total_particles = lons.shape[0]

rows = []
for hex_id, count in hex_counts.items():
    boundary = h3.cell_to_boundary(hex_id)
    polygon = Polygon([(lon, lat) for lat, lon in boundary])
    rows.append({
        'h3_id': hex_id,
        'beach_count': count,
        'probability': count / total_particles,
        'geometry': polygon
    })

if rows:
    hex_gdf = gpd.GeoDataFrame(rows, crs='EPSG:4326')
    hex_gdf = hex_gdf.sort_values('probability', ascending=False)

    print(f'\nTop 10 beaching hotspots:')
    print(hex_gdf[['h3_id', 'beach_count', 'probability']].head(10).to_string())
else:
    print('No beached particles found — skipping H3 aggregation')
    print('This could mean particles haven\'t reached coastlines in 90 days.')
    print('Try increasing the buffer distance or using a longer simulation.')
    hex_gdf = gpd.GeoDataFrame(columns=['h3_id', 'beach_count', 'probability', 'geometry'])

#
# Save OUTPUTS
#
hex_gdf.to_file('output/beaching_hotspots.geojson', driver='GeoJSON')
print(f'\nSaved: output/beaching_hotspots.geojson ({len(hex_gdf)} hexagons)')

final_gdf = gpd.GeoDataFrame(
    {'beached': beached_mask},
    geometry=[Point(lon, lat) for lon, lat in zip(final_lons, final_lats)],
    crs='EPSG:4326'
)
final_gdf.to_file('output/final_positions.geojson', driver='GeoJSON')
print(f'Saved: output/final_positions.geojson ({len(final_gdf)} points)')

# 
# PLOTS
# 
print('Creating plotz')

fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# Plot 1: All final particle positions
ax1 = axes[0]
not_beached_lons = [lon for lon, b in zip(final_lons, beached_mask) if not b]
not_beached_lats = [lat for lat, b in zip(final_lats, beached_mask) if not b]
ax1.scatter(not_beached_lons, not_beached_lats, s=1, alpha=0.3, c='steelblue', label='At sea')
ax1.scatter(beached_lons, beached_lats, s=3, alpha=0.5, c='red', label='Beached')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax1.set_title('Final Particle Positions (90 days)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: H3 beaching probability heatmap
ax2 = axes[1]
if len(hex_gdf) > 0:
    hex_gdf.plot(column='probability', cmap='YlOrRd', legend=True,
                 ax=ax2, edgecolor='gray', linewidth=0.3,
                 legend_kwds={'label': 'Beaching Probability'})
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Latitude')
ax2.set_title('Beaching Probability by H3 Hexagon')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('output/figures/beaching_hotspots.png', dpi=150)
print('Saved: output/figures/beaching_hotspots.png')
plt.show()

print('\nDone!')