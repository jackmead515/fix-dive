
gunicorn -w 4 -t 300 main:app

curl -v -F 'file=@clean_raw/chunk_0.mp4' http://127.0.0.1:8000/api/upload

mkdir -p /tmp/dive && mount -t tmpfs -o size=2G tmpfs /tmp/dive