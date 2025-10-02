# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Core framework for automated security research and web application testing.

This module provides the main framework components including configuration
management, database initialization, sandbox setup, and model registry
for the security research CLI application.
"""

from .config import Config
from .core import config_setup, init_rag_database, sandbox_setup, setup_model_registry

__all__ = [ Config, config_setup, init_rag_database, sandbox_setup, setup_model_registry ]