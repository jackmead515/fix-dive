import os

AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
S3_BUCKET = None

UPLOAD_BUFFER_SIZE = 1024 * 1024 * 10

POSTGRES_USER = None
POSTGRES_PASSWORD = None
POSTGRES_HOST = None
POSTGRES_PORT = None

def required_env(key):
    value = os.getenv(key)
    
    if value is None:
        raise Exception(f'{key} is not set in environment variables')
    
    return value


def initialize():
    global AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET, UPLOAD_BUFFER_SIZE
    global POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT

    S3_BUCKET = required_env('S3_BUCKET')
    AWS_ACCESS_KEY_ID = required_env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = required_env('AWS_SECRET_ACCESS_KEY')
    POSTGRES_USER = required_env('POSTGRES_USER')
    POSTGRES_PASSWORD = required_env('POSTGRES_PASSWORD')
    POSTGRES_HOST = required_env('POSTGRES_HOST')
    POSTGRES_PORT = required_env('POSTGRES_PORT')

    UPLOAD_BUFFER_SIZE = int(os.getenv('UPLOAD_BUFFER_SIZE', 1024 * 1024 * 10))
