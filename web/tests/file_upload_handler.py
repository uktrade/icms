from django.core.files.uploadhandler import TemporaryFileUploadHandler


class DummyFileUploadHandler(TemporaryFileUploadHandler):
    def receive_data_chunk(self, raw_data, start):
        return super().receive_data_chunk(raw_data, start)

    def file_complete(self, file_size):
        file = super().file_complete(file_size)

        # Set extra attributes the real file handlers add.
        file.original_name = f"original_name: {self.file_name}"
        file.file_size = file.size

        return file
