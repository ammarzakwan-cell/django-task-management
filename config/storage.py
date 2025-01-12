import os

config = {
    "disks": {
        "local": {
            "driver": "local",
            "root": "/"
        },
        "s3": {
            "driver": "s3",
            "s3": {
                "bucket": os.getenv("S3_BUCKET", "default-bucket-name"),
                "key": os.getenv("S3_KEY", ""),
                "secret": os.getenv("S3_SECRET", ""),
                "region": os.getenv("S3_REGION", "ap-southeast-1")  # Provide a default region if necessary
            }
        },
        "sftp_disk": {
            "driver": "sftp",
            "sftp": {
                "host": os.getenv("SFTP_HOST", "example.com"),
                "username": os.getenv("SFTP_USERNAME", "default_user"),
                "password": os.getenv("SFTP_PASSWORD", ""),
                "port": int(os.getenv("SFTP_PORT", 22))  # Convert port to an integer
            }
        }
    }
}
