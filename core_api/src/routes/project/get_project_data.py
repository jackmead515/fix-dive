from flask import Blueprint, Response, request
import polars as pl
import s3fs

import config

mod = Blueprint('get_project_data', __name__)

data_types = [
    'preprocess',
    'objects',
    'eye_tracking'
]

@mod.route('/api/projects/<string:project_id>/data/<string:data_type>', methods=['GET'])
def upload(project_id, data_type):
    
    if data_type not in data_types:
        return Response(f'invalid data type. Must be one of: {data_types}', status=400)

    # TODO: ensure schema validation is done here
    columns = request.args.get('columns')
    columns = columns.split(',') if columns else None

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
    data_key = f'{root_key}/{data_type}/{data_type}.gzip.parquet'
    
    full_key = f's3://{config.S3_BUCKET}/{data_key}'
    
    with s3.open(full_key, 'rb') as s3_file:
        df = pl.read_parquet(s3_file)
        
        if columns:
            df = df.select(columns)

        return Response(df.write_json(), mimetype='application/json')