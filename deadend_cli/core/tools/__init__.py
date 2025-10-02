# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Security research tools for AI agent interactions and automation.

This module provides a collection of tools that AI agents can use for
security research, including shell execution, HTTP requests, code analysis,
and knowledge base queries for comprehensive security assessments.
"""

from .shell import sandboxed_shell_tool
from .requester import send_payload, is_valid_request
from .webapp_code_rag import webapp_code_rag


__all__ = [ sandboxed_shell_tool, send_payload, is_valid_request, webapp_code_rag]