import structlog as logging
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from s3chunkuploader.file_handler import s3_client

from web.domains.file.models import File
from web.utils import FilevalidationService
from web.utils.s3upload import InvalidFileException, S3UploadService
from web.utils.virus import ClamAV, InfectedFileException

logger = logging.getLogger(__name__)


class PageTitleMixin(View):
    """Adds page title attribute of view to context"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        # Try get_page_title method first which takes precedence
        page_title = getattr(self, "get_page_title", None)
        if page_title:
            page_title = page_title()
        else:
            # Get page_title attribute if get_page_title doesn't exist
            page_title = getattr(self, "page_title", None)
        context["page_title"] = page_title
        return context


class DataDisplayConfigMixin(PageTitleMixin, ListView):
    """Adds display configuration for listed object"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        display = getattr(self, "Display", None)
        if display:
            context["display"] = display
        return context


class PostActionMixin(object):
    """Handle post requests with action variable: Calls method with the same
    name as action variable to handle action"""

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action:
            logger.debug(
                "Received post action", action=action, inputs=request.POST, args=args, kwargs=kwargs
            )
            if hasattr(self, action):
                return getattr(self, action)(request, *args, **kwargs)

        # If action does not exist continue with regular post request
        return super().post(request, *args, **kwargs)


class FileUploadMixin(FormView):
    """FormView mixin for processing file uploads."""

    # TODO: once the model is saved the files should be moved into
    #       its' destination folder

    _uploaded_file = None
    file_queryset = None

    def _create_file_entry(self, uploaded_file, **kwargs):
        """Create a file entry in the db for uploaded file"""
        return File.objects.create(
            filename=uploaded_file.original_name,
            file_size=uploaded_file.file_size,
            content_type=uploaded_file.content_type,
            browser_content_type=uploaded_file.content_type,
            description="",
            **kwargs,
        )

    def _upload(self, request):
        """Validates and virus scans the file uploaded to S3.

        A file is entry is created even if file validation is failed
        and file is deleted.

        File is uploaded by S3 Chunk Uploader.

        Invoked when post request received with paremter action="upload"
        see: web.view.mixins.PostActionMixin"""
        data = request.POST
        if not data:
            return HttpResponseBadRequest("Invalid body received")

        uploaded_file = request.FILES["uploaded_file"]

        try:
            file_path = None
            error_message = None

            upload_service = S3UploadService(
                s3_client=s3_client(),
                virus_scanner=ClamAV(
                    settings.CLAM_AV_USERNAME, settings.CLAM_AV_PASSWORD, settings.CLAM_AV_URL
                ),
                file_validator=FilevalidationService(),
            )

            file_path = upload_service.process_uploaded_file(
                settings.AWS_STORAGE_BUCKET_NAME, uploaded_file
            )

        except (InvalidFileException, InfectedFileException) as e:
            error_message = str(e)
        except Exception as e:
            logger.exception(e)
            error_message = "Unknown error uploading file"
        finally:
            self._uploaded_file = self._create_file_entry(
                uploaded_file,
                created_by=request.user,
                error_message=error_message,
                path=file_path,
            )

        # re render page
        return super().get(request)

    def _delete(self, request):
        file_id = request.POST.get("_file_id")
        File.objects.get(pk=file_id).archive()
        return super().get(request)

    def _restore(self, request):
        file_id = request.POST.get("_file_id")
        File.objects.get(pk=file_id).unarchive()
        return super().get(request)

    def post(self, request, *args, **kwargs):
        """Handle file actions"""
        if "_upload" in request.POST:
            return self._upload(request)

        if "_delete" in request.POST:
            return self._delete(request)

        if "_restore" in request.POST:
            return self._restore(request)

        # continue without actions
        return super().post(request, *args, **kwargs)

    def get_file_queryset(self):
        """Override this method or set file_queryset attribute of the view"""
        if self.file_queryset:
            return self.file_queryset

        return File.objects.none()

    def get_files(self):
        request = self.request
        if request.POST:
            # use posted file list with POST requests
            file_ids = request.POST.getlist("files")
            files = list(File.objects.filter(pk__in=file_ids).all())
            if "_upload" in request.POST:
                # prepend uploaded file to the list
                files.insert(0, self._uploaded_file)
        else:
            # read existing files from database
            files = self.get_file_queryset().all()

        return files

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files"] = self.get_files()
        return context
