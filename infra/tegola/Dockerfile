FROM gospatial/tegola:latest
COPY tegola_config.toml /opt/tegola_config.toml
COPY beaching_hotspots.gpkg /data/beaching_hotspots.gpkg
CMD ["serve", "--config", "/opt/tegola_config.toml"]