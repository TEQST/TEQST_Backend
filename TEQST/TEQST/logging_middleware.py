import logging
import json


class ContentLogging(object):

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.logger = logging.getLogger('django.request')
    
    def __call__(self, request):

        # log the request
        
        try:
            request_body = request.body.decode('utf-8')
            if 'password' in request_body:
                request_body = 'login data will not be logged'
        except UnicodeDecodeError:
            request_body = None

        response = self.get_response(request)

        if response.status_code >= 400:
            request_msg = 'Req: Method: ' + request.method
            if request_body:
                request_msg += ' body: ' + request_body
            else:
                request_msg += ' Could not decode request body'
            self.logger.warning(request_msg)
            self.logger.warning(f'Resp: Code: {response.status_code} {response.content.decode("utf-8")}')

        return response