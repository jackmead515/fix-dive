# Preprocesser

The preprocesser generates preliminary statistics on the master playlist
chunks by running parallel computation on it. It will detect motion, blur
detection, fast object detection, and other statistics. In addition, it 
will generate thumbnails, and different preview images and gifs
from the stream to display on the frontend.

It is meant to run quickly such that once the user has uploaded all
the dive footage, this can execute, and they can start to annotate
the dive and run other processes.

```
S3_ACCESS_KEY_ID=admin \
S3_SECRET_ACCESS_KEY=admin123 \
S3_BUCKET=fix-dive-storage \
PARALLEL_CHUNK_RATIO=0.05 \
S3_ENDPOINT_URL=http://172.23.0.100:30140 \
DASK_SCHEDULER_URL=tcp://172.23.0.100:32227 \
PROJECT_ID='1234567890' \
python3 main.py
```

mkdir -p /tmp/dive && sudo mount -t tmpfs -o size=2G tmpfs /tmp/dive