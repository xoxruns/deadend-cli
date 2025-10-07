# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Playwright-based HTTP request handler with enhanced session management and redirect handling."""

from typing import Dict, Any, Optional, Union, Tuple
from playwright.async_api import async_playwright
from rich.panel import Panel
from rich import box
from deadend_cli.cli.console import console_printer
from deadend_cli.core.tools.requester import analyze_http_request_text


class PlaywrightRequester:
    """
    Enhanced HTTP request handler using Playwright with headless browser.
    
    This class provides the same functionality as the raw socket Requester
    but with additional capabilities including automatic redirect handling,
    session management, cookie persistence, and improved error handling.
    """

    def __init__(self, verify_ssl: bool = True, proxy_url: Optional[str] = None):
        """
        Initialize the PlaywrightRequester.
        
        Args:
            verify_ssl (bool): Whether to verify SSL certificates
            proxy_url (str, optional): Proxy URL for requests
        """
        self.verify_ssl = verify_ssl
        self.proxy_url = proxy_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.request_context = None
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()

    async def _initialize(self):
        """Initialize Playwright browser and context."""
        if self._initialized:
            return

        self.playwright = await async_playwright().start()
        
        # Configure browser launch options
        browser_options = {
            'headless': True,
        }

        self.browser = await self.playwright.chromium.launch(**browser_options)

        # Configure browser context options
        context_options = {
            'ignore_https_errors': not self.verify_ssl,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

        if self.proxy_url:
            context_options['proxy'] = {'server': self.proxy_url}

        self.context = await self.browser.new_context(**context_options)
        self.request_context = self.context.request
        self._initialized = True

    async def _cleanup(self):
        """Clean up Playwright resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False

    async def send_raw_data(self, host: str, port: int, target_host: str, 
                          request_data: str, is_tls: bool = False, 
                          via_proxy: bool = False) -> Union[str, bytes]:
        """
        Send raw HTTP request data to a target host.
        
        This method provides the same interface as the original Requester.send_raw_data()
        but uses Playwright for enhanced functionality including automatic redirects
        and session management.
        
        Args:
            host (str): Host to connect to (proxy host if via_proxy=True)
            port (int): Port to connect to
            target_host (str): Target host for the actual request
            request_data (str): Raw HTTP request string
            is_tls (bool): Whether to use TLS encryption
            via_proxy (bool): Whether to route through a proxy
            
        Returns:
            Union[str, bytes]: Raw HTTP response or error message
        """
        if not self._initialized:
            await self._initialize()

        # Validate the HTTP request and report issues before sending
        valid, report = analyze_http_request_text(request_data)
        if not valid:
            issues = report.get('issues', [])
            reason = "\n".join(
                [f"- {msg}" for msg in issues]) if issues else "- Unknown validation error"
            error_message = (
                "Invalid HTTP request. The following issues were found:\n"
                f"{reason}\n\n--- Raw Request ---\n{request_data}"
            )
            return error_message

        # Parse the raw HTTP request
        parsed_request = self._parse_raw_request(request_data)
        if not parsed_request:
            return "Failed to parse HTTP request"

        # Build the target URL
        protocol = "https" if is_tls else "http"
        if via_proxy:
            # When using proxy, we need to construct the full URL
            target_url = f"{protocol}://{target_host}{parsed_request['path']}"
        else:
            # Direct connection
            target_url = f"{protocol}://{host}:{port}{parsed_request['path']}"

        try:
            # Send the request using Playwright
            response = await self._send_request(
                method=parsed_request['method'],
                url=target_url,
                headers=parsed_request['headers'],
                body=parsed_request['body'],
                follow_redirects=True,
                max_redirects=20
            )

            # Format the response similar to the original requester
            formatted_response = await self._format_response(response)

            # Display the response in a panel
            response_panel = Panel(
                formatted_response,
                title="[bold green]HTTP Response[/bold green]",
                border_style="green",
                box=box.ROUNDED
            )
            console_printer.print(response_panel)

            return formatted_response.encode('utf-8') if isinstance(formatted_response, str) else formatted_response

        except (ValueError, IndexError, AttributeError, ConnectionError) as e:
            error_message = f"Request failed: {str(e)}"
            error_panel = Panel(
                error_message,
                title="[bold red]Request Error[/bold red]",
                border_style="red",
                box=box.ROUNDED
            )
            console_printer.print(error_panel)
            return error_message.encode('utf-8')

    def _parse_raw_request(self, raw_request: str) -> Optional[Dict[str, Any]]:
        """
        Parse raw HTTP request string into components.
        
        Args:
            raw_request (str): Raw HTTP request string
            
        Returns:
            Optional[Dict[str, Any]]: Parsed request components or None if invalid
        """
        try:
            lines = raw_request.strip().split('\r\n')
            if not lines:
                return None

            # Parse request line
            request_line = lines[0]
            parts = request_line.split(' ', 2)
            if len(parts) < 2:
                return None

            method = parts[0]
            path = parts[1]

            # Parse headers
            headers = {}
            body_start = 0

            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()

            # Extract body
            body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''

            return {
                'method': method,
                'path': path,
                'headers': headers,
                'body': body
            }

        except (ValueError, IndexError, AttributeError):
            return None

    async def _send_request(self, method: str, url: str, headers: Dict[str, str], 
                          body: str, follow_redirects: bool = True, 
                          max_redirects: int = 20) -> Any:
        """
        Send HTTP request using Playwright's APIRequestContext.
        
        Args:
            method (str): HTTP method
            url (str): Target URL
            headers (Dict[str, str]): Request headers
            body (str): Request body
            follow_redirects (bool): Whether to follow redirects
            max_redirects (int): Maximum number of redirects to follow
            
        Returns:
            Any: Playwright response object
        """
        request_options = {
            'headers': headers,
            'max_redirects': max_redirects if follow_redirects else 0,
        }

        if body:
            request_options['data'] = body

        # Send request based on method
        method_upper = method.upper()
        if method_upper == 'GET':
            return await self.request_context.get(url, **request_options)
        elif method_upper == 'POST':
            return await self.request_context.post(url, **request_options)
        elif method_upper == 'PUT':
            return await self.request_context.put(url, **request_options)
        elif method_upper == 'DELETE':
            return await self.request_context.delete(url, **request_options)
        elif method_upper == 'HEAD':
            return await self.request_context.head(url, **request_options)
        elif method_upper == 'PATCH':
            return await self.request_context.patch(url, **request_options)
        else:
            # Use fetch for custom methods
            return await self.request_context.fetch(url, method=method_upper, **request_options)

    async def _format_response(self, response: Any) -> str:
        """
        Format Playwright response into HTTP response string.
        
        Args:
            response: Playwright response object
            
        Returns:
            str: Formatted HTTP response string
        """
        try:
            # Get response body
            body = await response.body()
            if isinstance(body, bytes):
                try:
                    body_text = body.decode('utf-8', errors='replace')
                except UnicodeDecodeError:
                    body_text = str(body)
            else:
                body_text = str(body)

            # Format response headers
            headers_text = ""
            for name, value in response.headers.items():
                headers_text += f"{name}: {value}\r\n"

            # Format status line
            status_line = f"HTTP/1.1 {response.status} {response.status_text or 'OK'}\r\n"

            # Combine all parts
            formatted_response = status_line + headers_text + "\r\n" + body_text

            return formatted_response

        except (UnicodeDecodeError, AttributeError, KeyError) as e:
            return f"Error formatting response: {str(e)}"

    async def get_cookies(self) -> Dict[str, str]:
        """
        Get current session cookies.
        
        Returns:
            Dict[str, str]: Dictionary of cookie name-value pairs
        """
        if not self._initialized or not self.context:
            return {}

        cookies = await self.context.cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}

    async def set_cookies(self, cookies: Dict[str, str], domain: str = None):
        """
        Set session cookies.
        
        Args:
            cookies (Dict[str, str]): Dictionary of cookie name-value pairs
            domain (str, optional): Cookie domain
        """
        if not self._initialized or not self.context:
            return

        cookie_list = []
        for name, value in cookies.items():
            cookie_dict = {
                'name': name,
                'value': value,
                'domain': domain or '.example.com',
                'path': '/'
            }
            cookie_list.append(cookie_dict)

        await self.context.add_cookies(cookie_list)

    async def clear_session(self):
        """Clear all session data (cookies, local storage, etc.)."""
        if not self._initialized or not self.context:
            return

        await self.context.clear_cookies()
        await self.context.clear_permissions()


async def send_payload_with_playwright(
    target_host: str,
    raw_request: str,
    proxy: bool = False,
    verify_ssl: bool = False
) -> Union[str, bytes]:
    """
    Send HTTP payload using Playwright with enhanced capabilities.
    
    This function provides the same interface as the original send_payload()
    but uses Playwright for improved functionality.
    
    Args:
        target_host (str): Target host in format "host:port" or URL
        raw_request (str): Raw HTTP request string
        proxy (bool): Whether to route through localhost:8080 proxy
        verify_ssl (bool): Whether to verify SSL certificates
        
    Returns:
        Union[str, bytes]: HTTP response or error message
    """
    def _parse_target(th: str) -> Tuple[str, int]:
        """Parse target host string into host and port."""
        # Remove protocol prefix first
        if th.startswith("http://"):
            th = th[7:]
            default_port = 80
        elif th.startswith("https://"):
            th = th[8:]
            default_port = 443
        else:
            default_port = 80

        parts = th.split(":")
        if len(parts) >= 2:
            # Check if the last part is actually a port number
            try:
                port_int = int(parts[-1])
                host = ":".join(parts[:-1])
                return host, port_int
            except ValueError:
                # Last part is not a number, so no port specified
                host = th
                return host, default_port
        else:
            host = th
            return host, default_port

    host, port = _parse_target(target_host)

    # Determine if we should use TLS (simplified detection)
    is_tls = port == 443 or target_host.startswith('https://')
    proxy_url = "http://localhost:8080" if proxy else None

    async with PlaywrightRequester(verify_ssl=verify_ssl, proxy_url=proxy_url) as playwright_req:
        response = await playwright_req.send_raw_data(
            host=host,
            port=port,
            target_host=target_host,
            request_data=raw_request,
            is_tls=is_tls,
            via_proxy=proxy
        )

        return response
