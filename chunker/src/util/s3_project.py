import os
import urllib

def convert_to_http(s3_url, http_host):
    """
    Convert an s3 url to an http url.
    
    Example:
    `s3://five-dive-storage/projects/12345/raw_videos/video.mp4`
    converts too
    `http://minio.kubby.ninja/five-dive-storage/projects/12345/raw_videos/video.mp4`
    """
    url = urllib.parse.urlparse(s3_url)
    netloc = url.netloc
    url = url._replace(scheme='http', netloc=http_host)
    url = url._replace(path=f'{netloc}{url.path}')
    return url.geturl()