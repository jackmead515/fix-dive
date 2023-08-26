import os

S3_ENDPOINT_URL = None
S3_ACCESS_KEY_ID = None
S3_SECRET_ACCESS_KEY = None
S3_BUCKET = None
DASK_SCHEDULER_URL = None
PROJECT_ID = None

def required_env(key):
    value = os.getenv(key)
    
    if value is None:
        raise Exception(f'{key} is not set in environment variables')
    
    return value


def initialize():
    global S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET
    global S3_ENDPOINT_URL, PROJECT_ID, DASK_SCHEDULER_URL

    S3_BUCKET = required_env('S3_BUCKET')
    S3_ENDPOINT_URL = required_env('S3_ENDPOINT_URL')
    S3_ACCESS_KEY_ID = required_env('S3_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY = required_env('S3_SECRET_ACCESS_KEY')
    DASK_SCHEDULER_URL = required_env('DASK_SCHEDULER_URL')
    PROJECT_ID = required_env('PROJECT_ID')