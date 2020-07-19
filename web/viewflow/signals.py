from django.dispatch import Signal

flow_cancelled = Signal(providing_args=["process"])
