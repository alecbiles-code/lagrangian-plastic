# Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgeos-dev libproj-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir parcels dask[complete] distributed \
    xarray zarr netCDF4 scipy scikit-learn geopandas shapely \
    cartopy h3 h3pandas copernicusmarine cdsapi matplotlib jupyter

WORKDIR /app
COPY . /app
EXPOSE 8888 8787
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--allow-root", "--no-browser"]
