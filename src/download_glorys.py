import copernicusmarine


copernicusmarine.subset(
    dataset_id='cmems_mod_glo_phy_my_0.083deg_P1D-m',
    variables=['uo', 'vo'],
    minimum_depth=0, maximum_depth=1,
    start_datetime='2020-01-01',
    end_datetime='2022-01-01',   
    output_directory='data/glorys/',
    output_filename='glorys_2020_2022_01.nc'
)

