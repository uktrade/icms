#!/usr/bin/env python
# -*- coding: utf-8 -*-
import structlog as logging

logger = logging.getLogger(__name__)


class Session:
    """
    Helper to manage session data for a request
    """

    def __init__(self, request):
        self.request = request

    def pop(self, key, default=None):
        "Remvove data from session and return"
        value = self.request.session.pop(key, default)
        logger.debug("Removed from session: {key=%s, value=%s} ", key, value)
        return value

    def put(self, key, value):
        "Add data to session with given key"
        self.request.session[key] = value
        logger.debug("Saved to session: {key=%s, value=%s} ", key, value)
