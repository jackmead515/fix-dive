import os
import base64
import os
import urllib

import s3fs

import config


def get_raw_video_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/raw_videos'


def get_playlist_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/playlists'


def get_raw_playlist_path(bucket_name, project_id, raw_file_path, etag):
    file_name = os.path.basename(raw_file_path)
    folder_name = base64.urlsafe_b64encode(f'{file_name}{etag}'.encode('utf-8')).decode('utf-8')
    #folder_name = urllib.parse.quote_plus(folder_name)
    
    return os.path.join(
        get_playlist_path(bucket_name, project_id),
        folder_name
    )

def get_raw_playlist_file(bucket_name, project_id, raw_file_path, etag, file_path):
    return os.path.join(
        get_raw_playlist_path(bucket_name, project_id, raw_file_path, etag),
        os.path.basename(file_path)
    )


def get_features_path(bucket_name, project_id):
    return f's3://{bucket_name}/projects/{project_id}/features'


def get_feature_file_path(bucket_name, project_id, raw_file_path, etag):
    file_name = os.path.basename(raw_file_path)
    file_name = base64.urlsafe_b64encode(f'{file_name}{etag}'.encode('utf-8')).decode('utf-8')
    #file_name = urllib.parse.quote_plus(file_name)
    
    return os.path.join(
        get_features_path(bucket_name, project_id),
        f'data_{file_name}.gzip.parquet'
    )


def generate_project(project_id):
    
    s3_client = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )

    allowed_file_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    raw_video_path = get_raw_video_path(config.S3_BUCKET, project_id)

    raw_file_paths = s3_client.ls(raw_video_path)
    raw_file_paths = [f's3://{path}' for path in raw_file_paths if os.path.splitext(path)[1] in allowed_file_extensions]

    raw_file_paths = [
        {
            'path': path,
            'etag': s3_client.info(path)['ETag'][1:-1],
            'name': os.path.basename(path),   
        } 
        for path in raw_file_paths
    ]

    feature_file_paths = [
        get_feature_file_path(config.S3_BUCKET, project_id, f['name'], f['etag'])
        for f in raw_file_paths
    ]
    
    playlist_file_paths = [
        get_raw_playlist_path(config.S3_BUCKET, project_id, f['path'], f['etag'])
        for f in raw_file_paths
    ]
    
    project_files = []
    for raw_file, feature_file, playlist_path in zip(raw_file_paths, feature_file_paths, playlist_file_paths):
        project_files.append({ 
            'raw_file': raw_file['path'],
            'feature_file': feature_file,
            'playlist_path': playlist_path,
        })

    return project_files
