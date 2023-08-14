# @profile_time('upload_features')
# def upload_features(s3_file, features):
#     dump = gzip.compress(pickle.dumps(features))
    
#     # generate int32 header of length of dump
#     length = struct.pack('i', len(dump))
    
#     # write header and dump to file
#     s3_file.write(length)
#     s3_file.write(dump)
    
    
# def process_features(raw_file, features_file):
#     s3 = s3fs.S3FileSystem(
#         anon=False,
#         key=config.AWS_ACCESS_KEY_ID,
#         secret=config.AWS_SECRET_ACCESS_KEY,
#     )

#     data = []
    
#     with s3.open(features_file, 'rb') as s3_file:
        
#         while True:
#             header = s3_file.read(4)

#             if not header:
#                 break
            
#             header = int.from_bytes(header, byteorder='little')
            
#             features = s3_file.read(header)
            
#             if not features:
#                 break
            
#             features = pickle.loads(gzip.decompress(features))
            
#             data.append([
#                 raw_file,
#                 features['frame_index'],
#                 features['blur'],
#                 len(features['objects']),
#                 *features['colors'],
#             ])

#     df = pd.DataFrame(data, columns=['file_path', 'frame_index', 'blur', 'total_objects', 'red', 'orange', 'yellow', 'green', 'blue', 'purple', 'white', 'black', 'brown'])

#     with s3.open(features_file, 'wb') as f:
#         df.to_parquet(f, index=False, compression='gzip')

#     print('process features complete', features)