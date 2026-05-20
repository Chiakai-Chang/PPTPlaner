"""
Enhanced error parsing for CLI-based agents.

Provides detailed error classification and user-friendly messages.
"""
import re
from typing import Dict, Optional, Tuple


class ErrorCategory:
    """Categories of agent errors."""
    AUTH = "auth"
    QUOTA = "quota"
    NETWORK = "network"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    CONFIG = "config"
    UNKNOWN = "unknown"


class ParsedError:
    """Container for parsed error information."""
    
    def __init__(
        self,
        category: str,
        message: str,
        raw_output: str,
        retryable: bool = True,
        user_action: Optional[str] = None
    ):
        self.category = category
        self.message = message
        self.raw_output = raw_output
        self.retryable = retryable
        self.user_action = user_action
    
    def __str__(self):
        return f"[{self.category.upper()}] {self.message}"


class CLIErrors:
    """Common CLI error patterns and their classifications."""
    
    # Authentication errors
    AUTH_PATTERNS = [
        (r"authentication.*failed", "Authentication failed. Please log in again."),
        (r"login.*required", "Login required. Run the CLI with login credentials."),
        (r"invalid.*token", "Invalid token. Your session may have expired."),
        (r"unauthorized", "Unauthorized access. Check your credentials."),
        (r"401", "HTTP 401: Authentication required."),
    ]
    
    # Quota errors
    QUOTA_PATTERNS = [
        (r"quota.*exceeded", "API quota exceeded. Please wait or upgrade your plan."),
        (r"rate.*limit", "Rate limit reached. Please try again later."),
        (r"429", "HTTP 429: Too many requests. Please slow down."),
        (r"daily.*limit", "Daily limit reached. Try again tomorrow."),
        (r"billing.*required", "Billing information required. Check your account."),
    ]
    
    # Network errors
    NETWORK_PATTERNS = [
        (r"connection.*refused", "Connection refused. Check if the service is running."),
        (r"timeout", "Request timed out. Check your network connection."),
        (r"dns.*resolve", "DNS resolution failed. Check your internet connection."),
        (r"network.*unreachable", "Network unreachable. Check your connection."),
        (r"502|503", "HTTP 502/503: Service temporarily unavailable. Retry later."),
    ]
    
    # Configuration errors
    CONFIG_PATTERNS = [
        (r"command.*not.*found", "Command not found. Ensure the agent is installed."),
        (r"invalid.*argument", "Invalid argument. Check your configuration."),
        (r"missing.*required", "Missing required configuration."),
    ]


def parse_cli_error(
    stderr: str,
    stdout: str = "",
    returncode: int = -1
) -> ParsedError:
    """
    Parse CLI error output and classify the error.
    
    Args:
        stderr: Standard error output
        stdout: Standard output (may contain error messages)
        returncode: Process return code
    
    Returns:
        ParsedError with classification and user-friendly message
    """
    combined = f"{stderr}\n{stdout}".lower()
    
    # Check authentication errors
    for pattern, message in CLIErrors.AUTH_PATTERNS:
        if re.search(pattern, combined):
            return ParsedError(
                category=ErrorCategory.AUTH,
                message=message,
                raw_output=f"{stderr}\n{stdout}",
                retryable=False,
                user_action="Check your authentication credentials and try again."
            )
    
    # Check quota errors
    for pattern, message in CLIErrors.QUOTA_PATTERNS:
        if re.search(pattern, combined):
            return ParsedError(
                category=ErrorCategory.QUOTA,
                message=message,
                raw_output=f"{stderr}\n{stdout}",
                retryable=True,
                user_action="Wait for quota to reset or consider upgrading your plan."
            )
    
    # Check network errors
    for pattern, message in CLIErrors.NETWORK_PATTERNS:
        if re.search(pattern, combined):
            return ParsedError(
                category=ErrorCategory.NETWORK,
                message=message,
                raw_output=f"{stderr}\n{stdout}",
                retryable=True,
                user_action="Check your internet connection and retry."
            )
    
    # Check configuration errors
    for pattern, message in CLIErrors.CONFIG_PATTERNS:
        if re.search(pattern, combined):
            return ParsedError(
                category=ErrorCategory.CONFIG,
                message=message,
                raw_output=f"{stderr}\n{stdout}",
                retryable=False,
                user_action="Check your agent configuration and installation."
            )
    
    # Default unknown error
    return ParsedError(
        category=ErrorCategory.UNKNOWN,
        message=f"Unknown error (code {returncode}): {stderr[:200] if stderr else 'No error message'}",
        raw_output=f"{stderr}\n{stdout}",
        retryable=True
    )


def format_error_for_user(parsed_error: ParsedError, agent_name: str) -> str:
    """
    Format error message for user display.
    
    Args:
        parsed_error: The parsed error
        agent_name: Name of the agent that failed
    
    Returns:
        User-friendly error message
    """
    lines = [
        f"\n{'='*60}",
        f"❌ {agent_name} 執行錯誤",
        f"{'='*60}",
        f"類型: {parsed_error.category.upper()}",
        f"描述: {parsed_error.message}",
        "",
    ]
    
    if parsed_error.user_action:
        lines.append(f"💡 建議操作:")
        lines.append(f"   {parsed_error.user_action}")
        lines.append("")
    
    if parsed_error.retryable:
        lines.append("⏳ 此錯誤可以自動重試")
    else:
        lines.append("⚠️  此錯誤需要手動處理")
    
    lines.append(f"{'='*60}\n")
    
    return "\n".join(lines)
