class FurtherInformationProcessMixin:
    """
        A process mixin to be used by processes that needs parallel Further Information
        Request flows


        See: web/domains/case/access/models.py for example usage with
        Importer/Exporter Access Requests
    """

    def get_fir_response_permission(self):
        """
            Returns permission required to respond to a Further Information Request
        """
        raise NotImplementedError

    def get_fir_response_team(self):
        """
            Returns the team FIR is to be requested from

            Team in addition with response permission protects FIR response task
        """
        raise NotImplementedError

    def get_fir_starter_permission(self):
        """
            Returns permission required to start/review/close fir
        """
        raise NotImplementedError

    def get_fir_template(self):
        """
            Returns template to populate initial request subject  and request detail
        """
        raise NotImplementedError

    def get_process_namespace(self):
        """
            Returns namespace for process
        """
        raise NotImplementedError

    def render_template_content(self, template, request):
        """
            Render template content with placeholder variables
        """
        raise NotImplementedError

    def render_template_title(self, template, request):
        """
            Renders template title  with placeholder variables
        """
        raise NotImplementedError

    def add_fir(self, fir):
        """
            Invoked when a new FIR process is started

            Parameter: fir - New Furhter Information Request
        """
        raise NotImplementedError
