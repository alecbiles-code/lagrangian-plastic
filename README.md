# Lagrangian Plastic Pathways & Beaching Risk Simulator

A start to finish geospatial pipeline that simulates where floating marine plastic travels and where it beaches. All powered by real ocean data, open-source tools, and deployed on Kubernetes (the most over engineered tile server ever deployed to a 2017 Lenovo ThinkPad)


[Lagrangian ocean analysis](<https://en.wikipedia.org/wiki/Lagrangian_ocean_analysis>)
---

## What This All Does

18,000 virtual plastic particles were/are released from the mouths of the world's 18 most polluting rivers and tracked for 90 days through real ocean currents and wind dataa. The simulation identifies which coastlines are most at risk from river-sourced plastic pollution.

The web map lets you scrub through time and watch particles disperse day by day, see where they accumulate on coastlines, and explore probable beaching hotspots.

---

## Results

| Metric | Value |
|---|---|
| Particles simulated | 18,000 |
| Source rivers | 18 (Lebreton et al 2017) |
| Simulation duration | 90 days |
| Beached particles | 10,817 (60%) |
| Coastal hotspot hexagons | 1,069 |
| Validation (30-day separation) | < 100 km for best drifter pairs |

---

## Architecture


Data Acquisition: GLORYS12 ocean currents, ERA5 winds, NOAA GDP drifters
        ↓
Processing: NetCDF to Zarr (Dask), ERA5 subsetting & resampling
        ↓
Simulation: OceanParcels, RK4 advection, windage kernel, 1hr timestep
        ↓
Analysis: Beaching detection, H3 hex aggregation, GDP drifter validation
        ↓
Infrastructure: Docker, minikube, Terraform, Tegola tile server, PMTiles
        ↓
Frontend: MapLibre GL JS, animated particle tracks, interactive timeline


---

## Data Sources

All data is free and publicly available.

| Dataset | Source | Purpose |
|---|---|---|
| GLORYS12 | Copernicus Marine Service | Ocean surface currents (1/12°, daily) |
| ERA5 | Copernicus Climate Data Store | 10m wind components |
| GDP Drifters | NOAA AOML | Trajectory validation |
| GSHHG | NOAA/SOEST | Global shoreline geometry |
| Coastal Vulnerability Index | USGS DDS-68 | Coastal risk classification |

River source locations are based on [Lebreton et al. (2017)](https://doi.org/10.1038/ncomms15611), which identified the top plastic-polluting rivers globally. Rivers in asia make up most of the pollution, contributing 86% of all river based plastic entering the ocean.

---

## Technical Details

### Simulation

Lagrangian particle tracking via **OceanParcels v3.1.4** with 4th-order Runge-Kutta advection.. A custom windage kernel applies 2% of 10m wind speed as additional drift on each particle, with proper meters-to-degrees conversion using latitude-dependent scaling. Particles that exit the data domain are removed via a StatusCode recovery kernel.

### Beaching Detection

Particles whose final position falls within 0.25° (~25 km) of the GSHHG coastline are classified as beached. Beaching counts are aggregated into H3 hexagonal cells at resolution 5 (252 km²) and normalized by total particles seeded to produce probability maps.

### Validation

10 NOAA GDP drifters active in January 2020 were selected. Virtual particles were seeded at identical starting positions and advected through the same velocity fields. Separation distance was computed at 6-hour intervals following Liu & Weisberg (2011). Results showed sub-100 km separation at 30 days for the best-performing drifter pairs, with all drifters showing correct bulk transport direction.

### Infrastructure

The Tegola vector tile server is containerized with Docker and deployed to a local Kubernetes cluster (minikube), managed entirely by Terraform with horizontal pod autoscaling! Static beaching layers are served as PMTiles. The frontend is built with MapLibre GL JS.

---

## Project Structure

```
```
lagrangian-plastic/
├── src/
│   ├── simulation.py              # Main particle simulation (OceanParcels)
│   ├── download_glorys.py         # GLORYS12 ocean current download
│   ├── download_era5.py           # ERA5 wind data download
│   ├── convert_zarr.py            # NetCDF to Zarr conversion (Dask)
│   ├── hotspot_analysis.py        # Beaching detection & H3 aggregation
│   ├── validate_drifters.py       # GDP drifter selection
│   ├── run_validation_sim.py      # validation particle simulation
│   ├── compute_separation.py      # separation distance & plots
│   ├── export_tracks_geojson.py   # export tracks for frontend
│   ├── export_animated_tracks.py  # export timestamped points for animation
│   └── make_gpkg.py               # GeoJSON to GeoPackage for Tegola
├── frontend/
│   ├── index.html                 # Interactive web map
│   ├── particle_tracks.geojson    # Sampled track lines
│   ├── particle_points.geojson    # Timestamped points for animation
│   ├── beaching_hotspots.geojson  # H3 hex beaching probabilities
│   └── beaching_hotspots.pmtiles  # Tiled hotspot layer
├── infra/
│   ├── main.tf                    # Terraform K8s deployment
│   └── tegola/
│       ├── Dockerfile             # Tegola container
│       └── tegola_config.toml     # Tile server configg
├── Dockerfile                     # science stack container
└── .gitignore
```

---

## Known Limitations

The land mask that I applied does not seem to work, and I can't figure out why.... so particles drift through coastlines and landmasses in some cases. Beaching detection uses a simple proximity buffer at the final timestep insted of continuous coastline interaction. The 90-day runtime misses longer gyre accumulation patterns. Windage is a flat 2% insted of a distribution reflecting variable debris buoyancy. Particle seeding is uniform across rivers rather than weighted by actual plastic discharge estimates.

---

## Stack

**Science:** Python, OceanParcels, Dask, xarray, GeoPandas, H3, SciPy

**Data:** GLORYS12, ERA5, NOAA GDP Drifters, GSHHG, USGS CVI

**Infrastructure:** Docker, Kubernetes (minikube), Terraform, Tegola, PMTiles, Tippecanoe

**Frontend:** MapLibre GL JS, Tailwind CSS

---

## References

- Lebreton, L. C. M. et al. (2017). River plastic emissions to the world's oceans. *Nature Communications*, 8, 15611.
- Yoon, J. H. et al. (2010). Estimation of the windage of floating marine debris. *Marine Pollution Bulletin*.
- Liu, Y. & Weisberg, R. H. (2011). Evaluation of trajectory modeling in different dynamic regions. *Journal of Atmospheric and Oceanic Technology*.
- Lange, M. & van Sebille, E. (2017). Parcels v0.9: prototyping a Lagrangian ocean analysis framework. *Geoscientific Model Development*.

---

Built by [Alec Biles](https://github.com/alecbiles-code)
