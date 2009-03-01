# -*- coding: utf-8 -*-

import re
class StripWhitespaceMiddleware:
    """
    Strips leading and trailing whitespace from response content.
    """
    def __init__(self):
        self.whitespace = re.compile('\s*\n')

    def process_response(self, request, response):
        if("text/html" in response['Content-Type'] ):
            new_content = self.whitespace.sub('\n', response.content)
            response.content = new_content
            return response
        else:
            return response