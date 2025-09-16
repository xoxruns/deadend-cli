import socket
from asgiref.sync import sync_to_async
import httptools
import ssl
from pydantic_ai import RunContext
from cli.console import console_printer

from .zap_connector import ZapConnector 
from ..utils.structures import *



class Requester:
    def __init__(self, verify_ssl, proxy_url='http://localhost:8080'):
        # Zap connection
        # super().__init__(api_key, proxy_url)
        # super().set_default_config()
        self.ssl_context = verify_ssl
    

    # async def open_url(self, url):
    #     self.url = url
    #     response = await self._zap_open_url(url=self.url)
    #     return response
    

    @sync_to_async
    def send_raw_data(self, host, port, target_host, request_data):
        # checking if the request received has an HTTP format. 
        bytes_request=request_data.encode('utf-8')
        # parsed_data = parse_http_request(bytes_request)
        # if parsed_data!=None: 
        console_printer.print(request_data)
        response = send_raw_request(host=host, port=port,target_host=target_host, request=bytes_request)
        return response
        # else: 
        #     # TODO: a better error handling must be done here to return why the request is malformed.
        #     return "Malformed HTTP request. Something is wrong with the request data, retry with another one."


def parse_http_request(raw_data):
    class RequestParser:
        def __init__(self):
            self.url = None
            self.headers = {}
            self.body = b''
            self.complete = False
        
        def on_url(self, url):
            self.url = url.decode('utf-8')
        
        def on_header(self, name, value):
            self.headers[name.decode('utf-8').lower()] = value.decode('utf-8')
        
        def on_body(self, body):
            self.body += body
        
        def on_message_complete(self):
            self.complete = True
    
    def _is_valid_request(parser):
        """
        this function validates an HTTP request. 
        it checks if the request we are about to send will be
        sent with the right data. 
        """

        if not parser.url or not parser.url.startswith('/'):
            return False

        required_headers = ["host"]
        for header in required_headers:
            if header not in parser.headers:
                return False
            
        # if 'content-length' in parser.headers:
        #     try:
        #         content_length = int(parser.headers['content-length'])
        #         if content_length < 0:
        #             return False
        #         if len(parser.body) != content_length:
        #             return False
        #     except ValueError:
        #         return False
        
        if 'content-length' in parser.headers and 'transfer-encoding' in parser.headers:
            if 'chunked' in parser.headers['transfer-encoding']:
                return False  # Can't have both Content-Length and chunked encoding
        
        method = parser.method if hasattr(parser, 'method') else None
        if method in ['POST', 'PUT', 'PATCH']:
            # These methods should have content-type for body data
            if not parser.body and len(parser.body)==0:
                return False
        return True

    try: 
        request_parser = RequestParser()
        parser = httptools.HttpRequestParser(request_parser)
        parser.feed_data(raw_data)
        if not request_parser.complete:
            print("Incomplete HTTP request.")
            return None
        if not _is_valid_request(request_parser):
            return None 
        return request_parser
    except httptools.HttpParserError:
        print("HTTPParserError : Malformed HTTP request.")
        return None 
    

def send_raw_request(host, port, target_host, request):
    # The ssl context here does not check the certificates
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.verify_flags = ssl.VERIFY_DEFAULT

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    response = ""
    try: 
        s.connect((host, port))
        sso = context.wrap_socket(s, server_hostname=target_host)
        sso.send(request)
        response = sso.recv(4096)
        sso.close()
        s.close()
    except socket.error as err: 
        print(f"An error has occured when sending request. :{err}".format(err))
        response = f"Request not send. Please retry. The error is : {err}".format(err)

    return response

def is_valid_request(ctx: RunContext[str], raw_request: str) -> bool:
    bytes_request=raw_request.encode('utf-8')
    parsed_data = parse_http_request(bytes_request)

    if parsed_data != None:
        return True
    else: 
        return False
            
async def send_payload(ctx: RunContext[str], target_host: str, raw_request:str, proxy: bool) -> str | bytes:
    requester = Requester(verify_ssl=False)
    # TODO: here the handling should be reviewed to work for all cases 
    # I don't think everything works here but we will keep it this way for now
    # Adding error handling could be great too. 
    # localhost:8080 is the proxy
    if proxy:
        response = await requester.send_raw_data(host='localhost', port=8080,target_host=target_host, request_data=raw_request)
    else:
        (host, port) = target_host.split(":")
        response = await requester.send_raw_data(host=host, port=int(port),target_host=target_host, request_data=raw_request)
    return response