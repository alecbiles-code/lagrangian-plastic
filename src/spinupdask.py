from dask.distributed import Client, LocalCluster

if __name__ == '__main__':
    cluster = LocalCluster(
        n_workers=4,
        threads_per_worker=2,
        memory_limit='4GB'
    )
    client = Client(cluster)
    print(f'Dashboard: {client.dashboard_link}')

    input('Press Enter to shut down...')