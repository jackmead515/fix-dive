from flask import Blueprint, request, Response
from werkzeug.utils import secure_filename
import s3fs

import config

mod = Blueprint('upload', __name__)

@mod.route('/api/upload', methods=['POST'])
def upload():
    
    # get request headers
    headers = request.headers
    
    # reject request if 'Content-Length' not in headers:
    if 'Content-Type' not in headers:
        return Response('Content-Type not in headers', status=400)

    # retrieve file from request
    upload_file = request.files['file']
    file_name = secure_filename(upload_file.filename)
    s3_file_path = f's3://{config.S3_BUCKET}/projects/1234567890/raw_videos/{file_name}'
    
    print('uploading', s3_file_path)
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )

    file_length = int(headers['Content-Length'])
    bytes_read = 0

    with s3.open(s3_file_path, 'wb') as s3_file:
        
            while True:
                data = upload_file.read(config.UPLOAD_BUFFER_SIZE)

                if not data:
                    break
                
                bytes_read += len(data)
                progress = round(bytes_read / file_length * 100, 2)
                print(f'{progress}%')
                
                s3_file.write(data)

    return 'OK', 200
    