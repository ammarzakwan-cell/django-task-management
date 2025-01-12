import logging
from pathlib import Path
import json
from fs.osfs import OSFS
from fs_s3fs import S3FS
#from fs.sftpfs import SFTPFS
from fs.errors import ResourceNotFound
from modules.media.models import Media
import boto3
from botocore.exceptions import ClientError
from config.storage import config

class StorageComponent:

    def __init__(self):
        self.config = config
        self.filesystem = {}
        self.active_disk = None
        self.disk_config = None
        self.default_disk = 'local'  # Default disk can be set here
        
    def get_adapter(self):
        """Return the adapter (filesystem) for the selected disk."""
        if self.active_disk in self.filesystem:
            return self.filesystem[self.active_disk]
        
        # If adapter is not already set, load the disk configuration
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
        except Exception as e:
            logging.error(f"Error initializing disk: {e}")
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
        except Exception as e:
            logging.error(f"Error creating SFTP driver: {e}") """

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
        except Exception as e:
            logging.error(f"Error creating S3 driver: {e}")

    def _create_local_driver(self):
        """Create local filesystem driver."""
        try:
            root = str(Path(self.disk_config.get('root', '/')).resolve())
            self.filesystem[self.active_disk] = OSFS(root)
        except Exception as e:
            logging.error(f"Error creating local driver: {e}")
    
    def write(self, path: str, content):
        """Store a file in the given filesystem."""
        try:
            # Open the path in binary write mode
            with self.get_adapter().open(path, 'wb') as file:
                if hasattr(content, 'chunks'):  # Handles Django UploadedFile objects
                    for chunk in content.chunks():
                        file.write(chunk)
                else:
                    # Ensure content is bytes
                    if isinstance(content, str):
                        content = content.encode()  # Convert string to bytes
                    file.write(content)  # Write bytes to file

            print(f"File '{path}' stored successfully.")
        except Exception as e:
            logging.error(f"Error storing file '{path}': {e}")


    def get(self, path: str) -> str:
        """Get the content of a file from the given filesystem."""
        try:
            return self.get_adapter().readtext(path)
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as e:
            logging.error(f"Error reading file '{path}': {e}")

    def remove(self, path: str):
        """Delete a file from the given filesystem."""
        try:

            self.get_adapter().remove(path)
            print(f"File '{path}' deleted successfully.")
        except ResourceNotFound:
            logging.error(f"File '{path}' not found.")
        except Exception as e:
            logging.error(f"Error deleting file '{path}': {e}")

    def is_exist(self, path: str) -> bool:
        """Check if a file exists in the given filesystem."""
        try:
            return self.get_adapter().exists(path)
        except Exception as e:
            logging.error(f"Error checking file existence for '{path}': {e}")
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
            print(f"File '{source_path}' uploaded to '{dest_path}' successfully.")
        except Exception as e:
            logging.error(f"Error uploading file '{source_path}' to '{dest_path}': {e}")

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
        except Exception as e:
            logging.error(f"Error listing directory '{directory}': {e}")
            return []
        
    def move(self, src_path: str, dst_path: str, overwrite: bool = False):
        try:
            return self.get_adapter().move(src_path, dst_path, overwrite)
        except Exception as e:
            logging.error(f"Error moving file '{src_path}' to '{dst_path}': {e}")

    def upload_file(self, file, model_instance, collection_name: str = "media"):

        # Generate file details
        file_name = file.name
        file_path = f"{collection_name}/{file_name}"  # Customize the S3 path
        mime_type = file.content_type
        file_size = file.size

        # Upload the file to S3
        self.write(file_path, file)

        # Create a Media entry
        Media.upsert(
            collection_name=collection_name,
            file_name=file_name,
            file_path=file_path,
            mime_type=mime_type,
            file_size=file_size,
            model_instance=model_instance
        )

    def get_public_url(self, file_path: str) -> str:
        """Generate a public URL for the given file."""
        return self.get_adapter().geturl(file_path)  # Ensure this generates the URL

    def generate_signed_url(self, object_name, expiration: int=3600):
        """
        Generate a presigned URL for accessing a file in S3.
        :param file_path: The S3 key (file path in the bucket)
        :param bucket_name: Name of the S3 bucket
        :param region: AWS region
        :param expiration: URL expiration time in seconds (default 1 hour)
        :return: Signed URL string
        """
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
        except ClientError as e:
            logging.error(f"Could not generate signed URL: {e}")
            return None


