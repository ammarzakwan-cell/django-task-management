import hashlib
import logging
import os
import time
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from fs.errors import ResourceNotFound
from fs.osfs import OSFS
from fs_s3fs import S3FS

from django.templatetags.static import static
from config.storage import config
from modules.media.models import Media


class StorageComponent:

    def __init__(self):
        self.config = config
        self.filesystem = {}
        self.active_disk = None
        self.disk_config = None
        self.default_disk = 'local'  # Default disk
        
    def get_adapter(self):
        """Return the adapter (filesystem) for the selected disk."""
        if self.active_disk in self.filesystem:
            return self.filesystem[self.active_disk]
        
        # set filesystem
        self.disk(self.active_disk)
        return self.filesystem.get(self.active_disk)

    def disk(self, disk: str = None):
        """Set the active disk and initialize the corresponding adapter."""
        self.active_disk = disk or self.default_disk

        if self.active_disk in self.filesystem:
            return self

        try:
            self.disk_config = self.config['disks'][self.active_disk]
            driver = self.disk_config['driver']
            if driver == 'sftp':
                self._create_sftp_driver()
            elif driver == 's3':
                self._create_s3_driver()
            else:
                self._create_local_driver()
        except Exception as exception:
            logging.error(f"Error initializing disk: {exception}")
        return self

    """ def _create_sftp_driver(self):
        #Create SFTP connection.
        try:
            sftp_config = self.disk_config.get('sftp', {})
            host = sftp_config.get('host')
            username = sftp_config.get('username')
            password = sftp_config.get('password')
            port = sftp_config.get('port', 22)
            
            self.filesystem[self.active_disk] = SFTPFS(f"sftp://{username}:{password}@{host}:{port}")
        except Exception as exception:
            logging.error(f"Error creating SFTP driver: {exception}") """

    def _create_s3_driver(self):
        """Create S3 connection."""
        try:
            s3_config = self.disk_config.get('s3')
            bucket = s3_config.get('bucket')
            aws_access_key_id = s3_config.get('key')
            aws_secret_access_key = s3_config.get('secret')
            region = s3_config.get('region')
            
            # Initialize the S3 filesystem
            self.filesystem[self.active_disk] = S3FS(
                bucket_name=bucket,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region=region
            )
        except Exception as exception:
            logging.error(f"Error creating S3 driver: {exception}")

    def _create_local_driver(self):
        """Create local filesystem driver."""
        try:
            root = str(Path(self.disk_config.get('root', '/')).resolve())
            self.filesystem[self.active_disk] = OSFS(root)
        except Exception as exception:
            logging.error(f"Error creating local driver: {exception}")
    
    def write(self, path: str, content):
        """Store a file in the given filesystem."""
        try:
            with self.get_adapter().open(path, 'wb') as file:
                if hasattr(content, 'chunks'):
                    for chunk in content.chunks():
                        file.write(chunk)
                else:
                    # Ensure content is bytes
                    if isinstance(content, str):
                        content = content.encode()
                    file.write(content)

        except Exception as exception:
            logging.error(f"Error storing file '{path}': {exception}")


    def get(self, path: str) -> str:
        """Get the content of a file from the given filesystem."""
        try:
            return self.get_adapter().readtext(path)
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as exception:
            logging.error(f"Error reading file '{path}': {exception}")

    def remove(self, path: str):
        """Delete a file from the given filesystem."""
        try:

            self.get_adapter().remove(path)
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as exception:
            logging.error(f"Error deleting file '{path}': {exception}")

    def is_exist(self, path: str) -> bool:
        """Check if a file exists in the given filesystem."""
        try:
            return self.get_adapter().exists(path)
        except Exception as exception:
            logging.error(f"Error checking file existence for '{path}': {exception}")
            return False

    def put(self, source_path: str, dest_path: str):
        """
        Upload a file from the local filesystem to the given filesystem.
        
        :param fs: Target filesystem (e.g., S3)
        :param source_path: Path of the file on the local filesystem
        :param dest_path: Path to store the file in the target filesystem
        """
        try:
            with open(source_path, 'rb') as local_file:
                self.get_adapter().writebytes(dest_path, local_file.read())
        except Exception as exception:
            logging.error(f"Error uploading file '{source_path}' to '{dest_path}': {exception}")

    def listing(self, directory: str = "/") -> list:
        """
        List files in the specified directory of the given filesystem.
        
        :param fs: Target filesystem (e.g., local or S3)
        :param directory: Directory path to list files from
        :return: List of file and directory names
        """
        
        try:
            return self.get_adapter().listdir(directory)
        except ResourceNotFound:
            logging.error(f"Directory '{directory}' not found.")
            return []
        except Exception as exception:
            logging.error(f"Error listing directory '{directory}': {exception}")
            return []
        
    def move(self, src_path: str, dst_path: str, overwrite: bool = False):
        try:
            return self.get_adapter().move(src_path, dst_path, overwrite)
        except Exception as exception:
            logging.error(f"Error moving file '{src_path}' to '{dst_path}': {exception}")

    def upload_file(self, file, model_instance, collection_name: str = "media") -> bool:

        try:
            file_name = file.name
            # Extract file extension, e.g., ".jpg" or ".pdf"
            _, ext = os.path.splitext(file_name)
            unique_name = f"{hashlib.sha256((str(time.time()) + '-' + str(uuid4())).encode('utf-8')).hexdigest()}{ext}"
            #unique_name = f"{hashlib.sha256(f"{time.time()}-{uuid4()}".encode('utf-8')).hexdigest()}{ext}"
            file_path = f"{collection_name}/{unique_name}"
            file.name = unique_name
            print(file_name, file.name)

            # Upload the file to S3
            self.write(file_path, file)

            # Upload or insert into Media model
            return Media.upsert(
                collection_name=collection_name,
                file_name=file_name,
                file_path=file_path,
                mime_type=file.content_type,
                file_size=file.size,
                disk=self.active_disk,
                model_instance=model_instance
            )
        except Exception as exception:
            logging.error(f"{exception}")
            return False


    def get_public_url(self, file_path: str) -> str:
        """Generate a public URL for the given file."""
        return self.get_adapter().geturl(file_path)

    def generate_signed_url(self, object_name, expiration: int=900):
        """
        Generate a presigned URL for accessing a file in S3.
        :param file_path: The S3 key (file path in the bucket)
        :param bucket_name: Name of the S3 bucket
        :param region: AWS region
        :param expiration: URL expiration time in seconds (default 15 minutes)
        :return: Signed URL string
        """
        if not self.is_exist(object_name):
            return static('img/not_found.webp')

        s3_config = self.disk_config.get('s3')
        s3_client = boto3.client(
            's3', 
            aws_access_key_id=s3_config.get('key'),
            aws_secret_access_key=s3_config.get('secret'),
            region_name=s3_config.get('region'),
            endpoint_url='https://s3.ap-southeast-5.amazonaws.com',
            )
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': s3_config.get('bucket'),
                    'Key': object_name,
                },
                ExpiresIn=expiration
            )
            return response
        except ClientError as exception:
            logging.error(f"Could not generate signed URL: {exception}")
            return None


