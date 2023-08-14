AWS_ACCESS_KEY_ID=AKIAQFVMQCMQKBP446UI \
AWS_SECRET_ACCESS_KEY=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 \
S3_BUCKET=fix-dive-storage \
python3 main.py

mkdir -p /tmp/dive && sudo mount -t tmpfs -o size=2G tmpfs /tmp/dive