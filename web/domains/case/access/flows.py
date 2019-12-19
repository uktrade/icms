# from viewflow import flow, frontend
# from viewflow.base import this, Flow
# from viewflow.flow.views import CreateProcessView, UpdateProcessView
#
# from .models import AccessRequestProcess
#
#
# def send_access_request_refused_email(activation):
#     print(activation.process.reference + ': ' + activation.process.response)
#
#
# @frontend.register
# class AccessRequestFlow(Flow):
#     process_class = AccessRequestProcess
#
#     start = (
#         flow.Start(
#             CreateProcessView,
#             fields=['request_type', 'organisation_name', 'organisation_address']
#         ).Permission(
#             auto_create=True
#         ).Next(this.review_submitted_requet_by_admin)
#     )
#
#     review_submitted_requet_by_admin = (
#         flow.View(
#             UpdateProcessView,
#             fields=['reference', 'request_type', 'organisation_name',
#                     'organisation_address', 'request_reason', 'agent_name',
#                     'agent_address', 'valid_request', 'response']
#         ).Permission(
#             auto_create=True
#         ).Next(this.check_valid)
#     )
#
#     check_valid = (
#         flow.If(lambda activation: activation.process.valid_request)
#             .Then(this.check_existing_exporter)
#             .Else(this.send_refused_request_email)
#     )
#
#     check_approve = (
#         flow.If(lambda activation: activation.process.response ==
#                                    AccessRequestProcess.APPROVED)
#             .Then(this.check_existing_exporter)
#             .Else(this.send_refused_request_email)
#     )
#
#     check_existing_exporter = (
#         flow.If(lambda activation: activation.process.organisation_name in ('aaa', 'bbb', 'ccc'))
#             .Then(this.check_known_user)
#             .Else(this.send_refused_request_email)
#     )
#
#     check_known_user = (
#         flow.If(lambda activation: activation.process.organisation_name in ('aaa', 'bbb', 'ccc'))
#             .Then(this.review_submitted_requet_by_team)
#             .Else(this.send_refused_request_email)
#     )
#
#     review_submitted_requet_by_team = (
#         flow.View(
#             UpdateProcessView,
#             fields=['reference', 'request_type', 'organisation_name',
#                     'organisation_address', 'request_reason', 'agent_name',
#                     'agent_address', 'valid_request']
#         ).Permission(
#             auto_create=True
#         ).Next(this.check_valid_team)
#     )
#
#     check_valid_team = (
#         flow.If(lambda activation: activation.process.valid_request)
#             .Then(this.approve_requet_by_admin)
#             .Else(this.send_refused_request_email)
#     )
#
#     approve_requet_by_admin = (
#         flow.View(
#             UpdateProcessView,
#             fields=['reference', 'request_type', 'organisation_name',
#                     'organisation_address', 'request_reason', 'agent_name',
#                     'agent_address', 'response']
#         ).Permission(
#             auto_create=True
#         ).Next(this.check_final_approval)
#     )
#
#     check_final_approval = (
#         flow.If(lambda activation: lambda activation: activation.process.response == AccessRequestProcess.APPROVED)
#             .Then(this.end)
#             .Else(this.send_refused_request_email)
#     )
#
#     review_submitted_requet = (
#         flow.View(
#             UpdateProcessView,
#             fields=["response"]
#         ).Permission(
#             auto_create=True
#         ).Next(this.check_approve)
#     )
#
#     send_refused_request_email = (
#         flow.Handler(
#             send_access_request_refused_email
#         ).Next(this.end)
#     )
#
#     end = flow.End()
