# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""HTTP request handling and raw socket communication utilities."""

import socket
import ssl
from asgiref.sync import sync_to_async
import httptools

from pydantic_ai import RunContext
from deadend_cli.cli.console import console_printer


class Requester:
    """Requester is a object that makes available methods for interacting with low-level sockets."""
    def __init__(self, verify_ssl, proxy_url='http://localhost:8080'):
        # Configure SSL context based on verification preference
        context = ssl.create_default_context()
        if not verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.verify_flags = ssl.VERIFY_DEFAULT
        self.ssl_context = context

    @sync_to_async
    def send_raw_data(self, host, port, target_host, request_data, *, is_tls=False, via_proxy=False):
        # checking if the request received has an HTTP format. 
        bytes_request=request_data.encode('utf-8')
        # Validate the HTTP request and report issues before sending
        valid, report = analyze_http_request_text(request_data)
        if not valid:
            issues = report.get('issues', [])
            reason = "\n".join([f"- {msg}" for msg in issues]) if issues else "- Unknown validation error"
            error_message = (
                "Invalid HTTP request. The following issues were found:\n"
                f"{reason}\n\n--- Raw Request ---\n{request_data}"
            )
            # console_printer.print(error_message)
            return error_message

        console_printer.print(request_data)
        response = send_raw_request(
            host=host,
            port=port,
            target_host=target_host,
            request=bytes_request,
            is_tls=is_tls,
            via_proxy=via_proxy,
            ssl_context=self.ssl_context,
        )
        console_printer.print(response)
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
            self.method = None
        
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
            return None
        # capture method name if available
        try:
            method_bytes = parser.get_method()
            if method_bytes is not None:
                request_parser.method = method_bytes.decode('utf-8')
        except Exception:
            pass
        if not _is_valid_request(request_parser):
            return None
        return request_parser
    except httptools.HttpParserError:
        # print("HTTPParserError : Malformed HTTP request.")
        return None
    

def analyze_http_request_text(raw_request_text: str) -> tuple[bool, dict]:
    """
    Analyze a raw HTTP request string and return (is_valid, report_dict).
    report_dict contains: {'issues': [str], 'method': str|None, 'url': str|None, 'headers': dict}
    """
    issues: list[str] = []
    method: str | None = None
    url: str | None = None
    headers: dict[str, str] = {}
    body = b""

    if not raw_request_text or raw_request_text.strip() == "":
        return False, { 'issues': ["Empty request"], 'method': None, 'url': None, 'headers': {} }

    try:
        raw_bytes = raw_request_text.encode('utf-8')
    except Exception:
        return False, { 'issues': ["Request is not UTF-8 encodable"], 'method': None, 'url': None, 'headers': {} }

    parsed = parse_http_request(raw_bytes)
    if parsed is None:
        issues.append("Malformed HTTP request: could not parse line/headers/body correctly")
        return False, { 'issues': issues, 'method': None, 'url': None, 'headers': {} }

    method = getattr(parsed, 'method', None)
    url = getattr(parsed, 'url', None)
    headers = getattr(parsed, 'headers', {}) or {}
    body = getattr(parsed, 'body', b"") or b""

    if not url or not url.startswith('/'):
        issues.append("Request line contains invalid or missing path (URL must start with '/')")

    if 'host' not in headers:
        issues.append("Missing required 'Host' header")

    if 'content-length' in headers and 'transfer-encoding' in headers and 'chunked' in headers.get('transfer-encoding', '').lower():
        issues.append("Both Content-Length and Transfer-Encoding: chunked present (invalid)")

    if method in ['POST', 'PUT', 'PATCH']:
        # If body is empty, warn; not always invalid but usually a mistake
        if len(body) == 0:
            issues.append(f"Method {method} usually carries a body but none was provided")

    return (len(issues) == 0), { 'issues': issues, 'method': method, 'url': url, 'headers': headers }


def _proxy_connect_tunnel(sock: socket.socket, target_host: str) -> bytes | None:
    """
    Open a CONNECT tunnel to target_host (host:port) via an existing proxy TCP socket.
    Returns the proxy response bytes (headers) if non-200, otherwise None when tunnel established.
    """
    def _recv_headers(s: socket.socket) -> bytes:
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
            if b"\r\n\r\n" in b"".join(chunks):
                break
        return b"".join(chunks)

    connect_req = (
        f"CONNECT {target_host} HTTP/1.1\r\n"
        f"Host: {target_host}\r\n"
        f"Connection: keep-alive\r\n\r\n"
    ).encode("utf-8")
    sock.sendall(connect_req)
    proxy_resp = _recv_headers(sock)
    status_line = proxy_resp.split(b"\r\n", 1)[0]
    if b" 200 " not in status_line:
        return proxy_resp or b"Proxy CONNECT failed"
    return None


def _attempt_tls_handshake(sock: socket.socket, server_name: str, *, verify: bool) -> tuple[bool, bool, bool, str | None, ssl.SSLSocket | None]:
    """
    Try a TLS handshake on the given TCP socket. Returns tuple:
    (tls_supported, verification_ok, client_cert_required, error_message, tls_socket)
    If handshake succeeds, tls_socket is returned; otherwise None.
    """
    try:
        if verify:
            ctx = ssl.create_default_context()
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.verify_flags = ssl.VERIFY_DEFAULT
        tls_sock = ctx.wrap_socket(sock, server_hostname=server_name, do_handshake_on_connect=True)
        return True, verify, False, None, tls_sock
    except ssl.SSLError as e:
        msg = str(e).lower()
        # Detects if TLS is speaking but cert verification failed
        if "certificate" in msg and ("verify" in msg or "self signed" in msg or "unknown ca" in msg or "hostname" in msg):
            return True, False, False, str(e), None
        # Detect client cert requirement alerts
        if "certificate required" in msg or "tlsv1 alert certificate required" in msg:
            return True, True, True, str(e), None
        # Handshake failure but likely TLS (e.g., protocol version)
        if "handshake failure" in msg or "protocol version" in msg or "wrong signature type" in msg:
            return True, False, False, str(e), None
        # Wrong version number/unknown protocol usually indicates plaintext HTTP, not TLS
        if "wrong version number" in msg or "unknown protocol" in msg or "http request" in msg:
            return False, False, False, str(e), None
        return False, False, False, str(e), None
    except Exception as e:
        return False, False, False, str(e), None


def detect_tls_support(host: str, port: int, *, via_proxy: bool, proxy_addr: tuple[str, int] | None = None, timeout: float = 5.0) -> dict:
    """
    Probe if the target supports TLS, whether verification passes, and if a client certificate is required.
    Returns dict: { 'is_tls': bool, 'verification_ok': bool | None, 'client_cert_required': bool | None, 'error': str | None }
    """
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.settimeout(timeout)
    try:
        if via_proxy:
            if not proxy_addr:
                proxy_addr = ("localhost", 8080)
            tcp.connect(proxy_addr)
            err = _proxy_connect_tunnel(tcp, f"{host}:{port}")
            if err is not None:
                return { 'is_tls': False, 'verification_ok': None, 'client_cert_required': None, 'error': err.decode('utf-8', 'ignore') }
        else:
            tcp.connect((host, port))

        # First try strict verification
        is_tls, verification_ok, cert_required, err_msg, tls_sock = _attempt_tls_handshake(tcp, host, verify=True)
        if is_tls and tls_sock is not None:
            try:
                tls_sock.close()
            except Exception:
                pass
            return { 'is_tls': True, 'verification_ok': True, 'client_cert_required': False, 'error': None }

        if is_tls and not verification_ok and not cert_required:
            # retry without verification to confirm TLS works
            try:
                # need a fresh TCP connection
                tcp2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp2.settimeout(timeout)
                if via_proxy:
                    proxy = proxy_addr or ("localhost", 8080)
                    tcp2.connect(proxy)
                    err2 = _proxy_connect_tunnel(tcp2, f"{host}:{port}")
                    if err2 is not None:
                        return { 'is_tls': False, 'verification_ok': None, 'client_cert_required': None, 'error': err2.decode('utf-8', 'ignore') }
                else:
                    tcp2.connect((host, port))
                is_tls2, verification_ok2, cert_required2, err_msg2, tls_sock2 = _attempt_tls_handshake(tcp2, host, verify=False)
                if is_tls2 and tls_sock2 is not None:
                    try:
                        tls_sock2.close()
                    except Exception:
                        pass
                    return { 'is_tls': True, 'verification_ok': False, 'client_cert_required': False, 'error': err_msg }
                return { 'is_tls': is_tls2, 'verification_ok': False, 'client_cert_required': cert_required2, 'error': err_msg2 or err_msg }
            except Exception as e:
                return { 'is_tls': True, 'verification_ok': False, 'client_cert_required': False, 'error': str(e) }

        if cert_required:
            return { 'is_tls': True, 'verification_ok': True, 'client_cert_required': True, 'error': err_msg }

        # Not TLS or unknown
        return { 'is_tls': False, 'verification_ok': None, 'client_cert_required': None, 'error': err_msg }
    finally:
        try:
            tcp.close()
        except Exception:
            pass


def send_raw_request(host, port, target_host, request, is_tls=False, via_proxy=False, ssl_context: ssl.SSLContext | None = None):
    """Send raw request to the target"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)

    def _recv_all(sock: socket.socket, header_only: bool = False) -> bytes:
        chunks = []
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
                if header_only and b"\r\n\r\n" in b"".join(chunks):
                    break
            except socket.timeout:
                break
        return b"".join(chunks)

    try:
        s.connect((host, port))

        conn: socket.socket | ssl.SSLSocket = s

        # If going through a proxy with TLS target, create a CONNECT tunnel first
        if via_proxy and is_tls:
            err = _proxy_connect_tunnel(conn, target_host)
            if err is not None:
                return err
            # Upgrade to TLS over the tunnel
            if ssl_context is None:
                ssl_context = ssl.create_default_context()
            server_name = target_host.split(":")[0]
            conn = ssl_context.wrap_socket(conn, server_hostname=server_name)

        # If direct TLS (no proxy)
        elif (not via_proxy) and is_tls:
            if ssl_context is None:
                ssl_context = ssl.create_default_context()
            server_name = target_host.split(":")[0]
            conn = ssl_context.wrap_socket(conn, server_hostname=server_name)

        # Now send the raw HTTP request bytes
        conn.sendall(request)

        # Read the full response
        response_bytes = _recv_all(conn)

        try:
            conn.close()
        finally:
            if conn is not s:
                try:
                    s.close()
                except Exception:
                    pass

        return response_bytes
    except socket.error as err:
        print(f"An error has occured when sending request. :{err}".format(err))
        return f"Request not send. Please retry. The error is : {err}".encode("utf-8")

def is_valid_request(ctx: RunContext[str], raw_request: str) -> bool:
    """
    Backwards-compatible boolean validity check.
    Use `is_valid_request_detailed` for a full report.
    """
    valid, _report = analyze_http_request_text(raw_request)
    return bool(valid)


def is_valid_request_detailed(ctx: RunContext[str], raw_request: str) -> dict:
    """
    Return a detailed validation report for the raw HTTP request.
    Schema:
    { 
      'is_valid': bool, 
      'issues': [str], 
      'method': str|None, 
      'url': str|None, 
      'headers': dict, 
      'raw_request': str
    }
    """
    valid, report = analyze_http_request_text(raw_request)
    return {
        'is_valid': bool(valid),
        'issues': report.get('issues', []),
        'method': report.get('method'),
        'url': report.get('url'),
        'headers': report.get('headers', {}),
        'raw_request': raw_request,
    }

async def send_payload(
    ctx: RunContext[str],
    target_host: str,
    raw_request:str,
    proxy: bool
    ) -> str | bytes:
    """Tool to send requests in raw"""
    requester = Requester(verify_ssl=False)
    def _parse_target(th: str):
        parts = th.split(":")
        if len(parts) == 2:
            h, p = parts[0], parts[1]
        else:
            h, p = th, "80"
        try:
            port_int = int(p)
        except ValueError:
            port_int = 80
        return h, port_int

    host, port = _parse_target(target_host)

    # Auto-detect TLS and certificate requirements
    detection = detect_tls_support(
        host=host,
        port=port,
        via_proxy=proxy,
        proxy_addr=("localhost", 8080) if proxy else None,
    )
    is_tls = bool(detection.get('is_tls'))

    if proxy:
        response = await requester.send_raw_data(
            host='localhost',
            port=8080,
            target_host=target_host,
            request_data=raw_request,
            is_tls=is_tls,
            via_proxy=True,
        )
    else:
        response = await requester.send_raw_data(
            host=host,
            port=port,
            target_host=target_host,
            request_data=raw_request,
            is_tls=is_tls,
            via_proxy=False,
        )
    return response
