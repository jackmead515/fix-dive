import os
import uuid

import s3fs

import config
import util.s3_project as s3_project

def generate_project(project_id):
    
    allowed_file_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.AWS_ACCESS_KEY_ID,
        secret=config.AWS_SECRET_ACCESS_KEY,
    )
    
    raw_video_path = s3_project.raw_video_path(config.S3_BUCKET, project_id)

    raw_file_paths = s3.ls(raw_video_path)
    raw_file_paths = [path for path in raw_file_paths if os.path.splitext(path)[1] in allowed_file_extensions]

    raw_file_names = [
        {
            'etag': s3.info(path)['ETag'][1:-1],
            'name': os.path.basename(path).split('.')[0],   
        } 
        for path in raw_file_paths
    ]

    feature_file_paths = [
        s3_project.feature_file_path(config.S3_BUCKET, project_id, f['name'], f['etag'])
        for f in raw_file_names
    ]

    files = list(zip(
        raw_file_paths,
        feature_file_paths
    ))

    return files