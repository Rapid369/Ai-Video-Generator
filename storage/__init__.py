import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app, url_for
import uuid
from werkzeug.utils import secure_filename

class StorageManager:
    """Manager for cloud storage operations."""

    def __init__(self, app=None):
        self.app = app
        self.s3_client = None
        self.bucket_name = None
        self.use_s3 = False

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the storage manager with the Flask app."""
        self.app = app

        # Check if S3 is configured
        aws_access_key = app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = app.config.get('AWS_SECRET_ACCESS_KEY')
        self.bucket_name = app.config.get('AWS_S3_BUCKET_NAME')

        if aws_access_key and aws_secret_key and self.bucket_name:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=app.config.get('AWS_REGION', 'us-east-1')
            )
            self.use_s3 = True

    def save_file(self, file_data, directory, filename=None, content_type=None):
        """Save a file to storage.

        Args:
            file_data: The file data to save (bytes or file-like object)
            directory: The directory to save the file in
            filename: The filename to use (if None, a random UUID will be generated)
            content_type: The content type of the file

        Returns:
            The path to the saved file
        """
        if filename is None:
            # Generate a random filename with UUID
            ext = '.bin'
            if content_type:
                if content_type == 'image/jpeg':
                    ext = '.jpg'
                elif content_type == 'image/png':
                    ext = '.png'
                elif content_type == 'video/mp4':
                    ext = '.mp4'
                elif content_type == 'audio/mpeg':
                    ext = '.mp3'

            filename = f"{uuid.uuid4()}{ext}"
        else:
            # Secure the filename
            filename = secure_filename(filename)

        # Create the full path
        file_path = os.path.join(directory, filename)

        if self.use_s3:
            # Save to S3
            try:
                # Convert file_data to bytes if it's a file-like object
                if hasattr(file_data, 'read'):
                    file_data = file_data.read()

                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type

                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=file_data,
                    **extra_args
                )

                return file_path
            except ClientError as e:
                current_app.logger.error(f"Error uploading file to S3: {e}")
                # Fall back to local storage
                pass

        # Save to local storage
        local_path = os.path.join(current_app.static_folder, file_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Save the file
        with open(local_path, 'wb') as f:
            # Convert file_data to bytes if it's a file-like object
            if hasattr(file_data, 'read'):
                f.write(file_data.read())
            else:
                f.write(file_data)

        return file_path

    def get_file_url(self, file_path):
        """Get the URL for a file.

        Args:
            file_path: The path to the file

        Returns:
            The URL to access the file
        """
        if self.use_s3:
            try:
                # Generate a presigned URL
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_path
                    },
                    ExpiresIn=3600  # URL expires in 1 hour
                )
                return url
            except ClientError as e:
                current_app.logger.error(f"Error generating presigned URL: {e}")
                # Fall back to local URL
                pass

        # Return local URL
        return url_for('static', filename=file_path, _external=True)

    def delete_file(self, file_path):
        """Delete a file from storage.

        Args:
            file_path: The path to the file

        Returns:
            True if the file was deleted, False otherwise
        """
        if self.use_s3:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return True
            except ClientError as e:
                current_app.logger.error(f"Error deleting file from S3: {e}")
                # Fall back to local deletion
                pass

        # Delete from local storage
        local_path = os.path.join(current_app.static_folder, file_path)

        if os.path.exists(local_path):
            os.remove(local_path)
            return True

        return False

# Create a default storage manager instance
storage_manager = StorageManager()
