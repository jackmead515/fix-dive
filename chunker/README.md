# Chunker

The Chunker service will take all the raw videos from a project, parse them into
seperate HLS streams, and then generate a cohesive master playlist from them.

```sh
S3_ACCESS_KEY_ID=admin \
S3_SECRET_ACCESS_KEY=admin123 \
S3_BUCKET=fix-dive-storage \
S3_ENDPOINT_URL=http://172.23.0.100:30140 \
PROJECT_ID='1234567890' \
python3 main.py
```

```
s3fs \
    fix-dive-storage/projects/1234567890 \
    /tmp/dive/329825be-b687-418e-92e4-3b67f8ef2e09 \
    -o use_path_request_style,url=http://172.23.0.100:30140,parallel_count=16
```