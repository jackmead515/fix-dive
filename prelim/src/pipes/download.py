import config

def download_video(s3_client, s3_file_path, temp_file):  
    with s3_client.open(s3_file_path, 'rb') as s3_file:
        
        s3_info = s3_file.info()
        
        file_size = s3_info['Size']
        bytes_read = 0
        
        while True:
            data = s3_file.read(config.READ_BUFFER_SIZE)

            if not data:
                break
            
            bytes_read += len(data)
            progress = round(bytes_read / file_size * 100, 2)
            print(f'download progress: {progress}%', end='\r')
            
            temp_file.write(data)
    
    print('download complete')