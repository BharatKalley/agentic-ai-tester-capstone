import time
import random
import logging
from functools import wraps

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = Exception

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries=5,
    initial_wait_seconds=1,
    max_wait_seconds=60,
    exponential_base=2,
    jitter=True
):
    """
    Decorator that adds exponential backoff retry logic for API calls.
    
    Handles ResourceExhausted (429) errors from Gemini API quota limits.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_wait_seconds: Initial wait time before first retry
        max_wait_seconds: Maximum wait time between retries
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter to avoid thundering herd
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = initial_wait_seconds
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ResourceExhausted as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate wait time with exponential backoff
                        wait_time = min(
                            initial_wait_seconds * (exponential_base ** attempt),
                            max_wait_seconds
                        )
                        
                        # Add jitter to prevent thundering herd
                        if jitter:
                            wait_time += random.uniform(0, wait_time * 0.1)
                        
                        logger.warning(
                            f"API quota exceeded (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {wait_time:.2f} seconds... {e}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded. "
                            f"Unable to complete API request."
                        )
            
            # If we exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator
