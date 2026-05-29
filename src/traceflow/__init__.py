"""
TraceFlow — A lightweight Python decorator for visually tracing function execution.

Usage:
    from traceflow import watch

    @watch()
    def my_function(x):
        return x * 2

Global controls:
    import traceflow
    traceflow.disable()
    traceflow.enable()
    traceflow.is_enabled()
"""

from traceflow.core import watch, enable, disable, is_enabled

__version__ = "1.3.0"
__author__ = "Aarav Agarwal"
__all__ = ["watch", "enable", "disable", "is_enabled"]
