"""
Unit tests for CLI error parsing.
"""
import pytest
from agents.error_parser import (
    parse_cli_error,
    format_error_for_user,
    ErrorCategory,
    ParsedError
)


class TestCLIParsing:
    """Test CLI error parsing and classification."""
    
    def test_auth_error_detection(self):
        """Test authentication error detection."""
        stderr = "Error: Authentication failed. Please login."
        parsed = parse_cli_error(stderr)
        
        assert parsed.category == ErrorCategory.AUTH
        assert not parsed.retryable
        assert "Authentication" in parsed.message
    
    def test_quota_error_detection(self):
        """Test quota exceeded error detection."""
        stderr = "API quota exceeded. Try again later."
        parsed = parse_cli_error(stderr)
        
        assert parsed.category == ErrorCategory.QUOTA
        assert parsed.retryable
        assert "quota" in parsed.message.lower()
    
    def test_network_error_detection(self):
        """Test network error detection."""
        stderr = "Connection refused. Network unreachable."
        parsed = parse_cli_error(stderr)
        
        assert parsed.category == ErrorCategory.NETWORK
        assert parsed.retryable
    
    def test_http_429_error(self):
        """Test HTTP 429 rate limit detection."""
        stderr = "HTTP 429: Too Many Requests"
        parsed = parse_cli_error(stderr)
        
        assert parsed.category == ErrorCategory.QUOTA
        assert parsed.retryable
    
    def test_unknown_error(self):
        """Test unknown error handling."""
        stderr = "Some unexpected error occurred"
        parsed = parse_cli_error(stderr, returncode=1)
        
        assert parsed.category == ErrorCategory.UNKNOWN
        assert parsed.retryable
    
    def test_error_formatting(self):
        """Test user-friendly error formatting."""
        parsed = parse_cli_error("Authentication failed.")
        formatted = format_error_for_user(parsed, "Test Agent")
        
        assert "Test Agent" in formatted
        assert "AUTH" in formatted
        assert "Authentication" in formatted
    
    def test_parsed_error_str(self):
        """Test ParsedError string representation."""
        parsed = ParsedError(
            category=ErrorCategory.QUOTA,
            message="Quota exceeded",
            raw_output="test"
        )
        
        assert "QUOTA" in str(parsed)
        assert "Quota exceeded" in str(parsed)
    
    def test_case_insensitive_matching(self):
        """Test that error matching is case-insensitive."""
        stderr = "AUTHENTICATION FAILED (uppercase)"
        parsed = parse_cli_error(stderr)
        
        assert parsed.category == ErrorCategory.AUTH
    
    def test_user_action_included(self):
        """Test that user action is included for known errors."""
        stderr = "Connection refused"
        parsed = parse_cli_error(stderr)
        
        assert parsed.user_action is not None
        assert "connection" in parsed.user_action.lower()
