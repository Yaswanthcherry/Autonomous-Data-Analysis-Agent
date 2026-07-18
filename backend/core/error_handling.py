"""
Error handling utilities — circuit breakers, retries, and exception handling.
"""
import time
import functools
from typing import Callable, Type, Tuple, Any
from loguru import logger


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls.
    Prevents cascading failures by opening after threshold failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable) -> Callable:
        """Decorator to wrap a function with circuit breaker logic."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == "open":
                if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker transitioning to half-open")
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is open. Retry after {self.recovery_timeout} seconds."
                    )

            try:
                result = func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info("Circuit breaker closed after successful call")
                return result
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                logger.warning(
                    f"Circuit breaker failure {self.failure_count}/{self.failure_threshold}: {e}"
                )
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                    logger.error("Circuit breaker opened due to repeated failures")
                raise

        return wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Retry decorator with exponential backoff.
    Retries function on specified exceptions with increasing delay.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


# Pre-configured circuit breakers for common services
openai_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    expected_exception=Exception,  # OpenAI API errors
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=10.0,
    expected_exception=Exception,  # Database connection errors
)
