from dataclasses import dataclass
import os
import base64
import os

allowed_file_extensions = ['.mp4', '.avi', '.mov', '.mkv']



@dataclass
class Project:
    
    bucket_name: str
    """Name of the S3 bucket where the project is stored."""
    
    project_id: str
    """Id of the project"""
    
    raw_video_path: str
    """Full S3 path to the raw video files for this project."""
    
    features_path: str
    """Full S3 path to the feature files for this project."""
    
    playlists_path: str
    """Full S3 path to the playlists for this project."""
    
    playlist_variants: list


    def __init__(self, bucket_name, project_id):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.raw_video_path = f's3://{bucket_name}/projects/{project_id}/raw_videos'
        self.features_path = f's3://{bucket_name}/projects/{project_id}/features'
        self.playlists_path = f's3://{bucket_name}/projects/{project_id}/playlists'
        self.playlist_variants = ['low', 'view']

    
    def get_variant_playlist_path(self, variant: str):
        return os.path.join(self.playlists_path, f'{variant}.m3u8')


    def get_variant_playlist_segments(self, variant: str):
        return os.path.join(self.playlists_path, f'{variant}_segments.json')


    def get_variant_playlist_details(self, variant: str):
        return os.path.join(self.playlists_path, f'{variant}_details.json')


    def list_raw_videos_files(self, s3_client):
        """
        Returns a list of all the raw videos for this project
        with full s3 paths.
        
        Example: `s3://five-dive-storage/projects/12345/raw_videos/video.mp4`
        """
        raw_video_files = s3_client.ls(self.raw_video_path)

        return [
            f's3://{path}' for path in raw_video_files 
            if os.path.splitext(path)[1] in allowed_file_extensions
        ]


    def list_feature_files(self, s3_client):
        """
        Returns a list of all the existing feature files for this project.
        
        Example: `s3://five-dive-storage/projects/12345/features/data_MTIzNDU2Nzg5MA==.gz.parquet`
        """
        return [f's3://{path}' for path in s3_client.ls(self.features_path)]


    def list_playlist_folders(self, s3_client):
        """
        Lists all the playlists for this project regardless 
        of whether they exist or not. Playlist paths are generated
        from the file path and etag of the raw video files.
        
        Example:
        ```
            ['s3://five-dive-storage/projects/12345/playlists/MTIzNDU2Nzg5MA==']
        ```
        """
        raw_video_files = self.list_raw_videos_files(s3_client)
        
        raw_file_etags = [
            s3_client.info(path)['ETag'][1:-1]
            for path in raw_video_files
        ]

        return [
            os.path.join(self.playlists_path, etag)
            for etag in raw_file_etags
        ]