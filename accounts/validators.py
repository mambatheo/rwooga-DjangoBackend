from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class FileSizeValidator:
      
    def __init__(self, max_mb):
        self.max_mb = max_mb
        self.max_bytes = max_mb * 1024 * 1024  
    
    def __call__(self, file):
        if file.size > self.max_bytes:
            raise ValidationError(
                f'File size cannot exceed {self.max_mb}MB. '
                f'Current file size: {file.size / (1024 * 1024):.2f}MB'
            )
    
    def __eq__(self, other):
        return (
            isinstance(other, FileSizeValidator) and
            self.max_mb == other.max_mb
        )



validate_image_size = FileSizeValidator(max_mb=10)  # 10MB for images
validate_video_size = FileSizeValidator(max_mb=100)  # 100MB for videos
validate_document_size = FileSizeValidator(max_mb=50)  # 50MB for documents/3D files