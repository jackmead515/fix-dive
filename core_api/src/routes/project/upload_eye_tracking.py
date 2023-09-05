from flask import Blueprint, request, Response
import polars as pl
import s3fs

import config

mod = Blueprint('upload_project_eye_project', __name__)

@mod.route('/api/projects/<string:project_id>/upload/eye_tracking', methods=['POST'])
def upload(project_id):
    
    df = pl.read_csv(source=request.data, has_header=True, separator=',', dtypes={
        'progress': pl.Float64,
        'eye_x': pl.Float64,
        'eye_y': pl.Float64,
    })
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )
    
    root_key = f'projects/{project_id}/features'
    data_key = f'{root_key}/eye_tracking/eye_tracking.gzip.parquet'
    full_key = f's3://{config.S3_BUCKET}/{data_key}'
    
    with s3.open(full_key, 'wb') as s3_file:
        df.write_parquet(s3_file, compression='gzip')

    return 'OK', 200
    