import os
import base64

def raw_video_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/raw_videos'

def preliminary_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/preliminary'

def features_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/features'

def feature_file_path(bucket_name, project_id, raw_file_path, etag):
    file_name = os.path.basename(raw_file_path)
    file_name = os.path.splitext(file_name)[0]
    file_name = base64.b64encode(f'{file_name}{etag}'.encode('utf-8')).decode('utf-8')
    
    return os.path.join(
        features_path(bucket_name, project_id),
        f'data_{file_name}.gzip.parquet'
    )
