import os

AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
S3_BUCKET = None

READ_BUFFER_SIZE = 1024 * 1024 * 10

def required_env(key):
    value = os.getenv(key)
    
    if value is None:
        raise Exception(f'{key} is not set in environment variables')
    
    return value


def initialize():
    global AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET, READ_BUFFER_SIZE

    S3_BUCKET = required_env('S3_BUCKET')
    AWS_ACCESS_KEY_ID = required_env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = required_env('AWS_SECRET_ACCESS_KEY')

    READ_BUFFER_SIZE = int(os.getenv('READ_BUFFER_SIZE', 1024 * 1024 * 10))
