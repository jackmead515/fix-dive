from dask.distributed import Client

import config

def get_dask_client():
    return Client(address=config.DASK_SCHEDULER_URL)