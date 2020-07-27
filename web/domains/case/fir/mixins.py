class FurtherInformationProcessMixin:
    """
        A process mixin to be used by processes that needs parallel Further Information
        Request flows.
    """

    def fir_config(self):
        """
            Returns configuration required for FIR processes to run.

            Example Config:

            {
                'requester_permission': 'web.IMP_CASE_OFFICER',
                'responder_permission': 'web.IMP_EDIT_APP',
                'responder_team': 'web.IMP_EDIT_APP',
                'namespace': 'access:importer'
            }

        """
        raise NotImplementedError

    def fir_content(self, request):
        """
            Returns initial FIR content for requester to edit.

            Example:

            {
                'request_subject': 'subject',
                'request_detail': 'detail',
            }
        """
        raise NotImplementedError

    def on_fir_create(self, fir):
        """
            Invoked when a new FIR process is started.
            Returns a FurtherInformationRequest instance

            Parameter: fir - New Furhter Information Request
        """
        raise NotImplementedError
