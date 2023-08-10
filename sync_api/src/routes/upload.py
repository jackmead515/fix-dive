import io

from flask import Blueprint, request, Response
import s3fs
from werkzeug.utils import secure_filename

mod = Blueprint('upload', __name__)

@mod.route('/upload', methods=['POST'])
def upload():
    
    # get request headers
    headers = request.headers
    
    print(headers)
    
    # reject request if 'Content-Length' not in headers:
    if 'Content-Type' not in headers:
        return Response('Content-Type not in headers', status=400)

    # retrieve file from request
    upload_file = request.files['file']
    
    file_name = secure_filename(upload_file.filename)
    
    s3_file_path = f's3://jam-general-storage/{file_name}'
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key='AKIAQFVMQCMQKBP446UI',
        secret='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',
    )

    buffer_size = 1024 * 1024 * 10
    file_length = int(headers['Content-Length'])
    bytes_read = 0

    with s3.open(s3_file_path, 'wb') as s3_file:
        
            while True:
                data = upload_file.read(buffer_size)

                if not data:
                    break
                
                bytes_read += len(data)
                progress = round(bytes_read / file_length * 100, 2)
                print(f'{progress}%')
                
                s3_file.write(data)

    return 'OK', 200
    