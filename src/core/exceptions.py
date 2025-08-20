
class DeadendError(Exception):
    """Base exception deadend"""

class ModelProviderError(DeadendError):
    """Model provider specific errors"""

class AgentTimeoutError(DeadendError):
    """Analysis exceeded timeout"""

class VulnerabilityTestingError(DeadendError):
    """Error during vulnerability testing"""