"""
Core implementation of the TraceFlow @watch decorator.

This module contains all tracing logic: call tree rendering, timing,
variable state tracking, truncation, exception handling, and async support.
"""

import functools
import contextvars
import inspect
import time as _time
import sys as _sys

# ── Global State ────────────────────────────────────────────────

_depth = contextvars.ContextVar('depth', default=0)
_enabled = True


def enable():
    """Enable all tracing globally."""
    global _enabled
    _enabled = True


def disable():
    """Disable all tracing globally. Decorated functions still execute normally."""
    global _enabled
    _enabled = False


def is_enabled():
    """Return whether tracing is currently enabled."""
    return _enabled


# ── Decorator ───────────────────────────────────────────────────

def watch(func=None, *, track_time=True, truncate_len=50, max_depth=None, export_path=None, track_vars=False):
    """
    Decorator that traces function calls, producing an indented call tree.

    Args:
        track_time (bool): Append execution time to each return line. Default True.
        truncate_len (int): Max characters for argument/return repr. 0 or None to disable.
        max_depth (int): Stop tracing beyond this call depth. None for unlimited.
        export_path (str): Write trace output to this file instead of stdout.
        track_vars (bool): Log local variable assignments inside the function (sync only).

    Returns:
        The decorated function (sync or async wrapper).

    Example::

        @watch(track_time=True)
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)

        fibonacci(3)
        # fibonacci(3)
        # ├── fibonacci(2)
        # │   ├── fibonacci(1)
        # │   │   └── return 1 [0.0003s]
        # │   ├── fibonacci(0)
        # │   │   └── return 0 [0.0000s]
        # │   └── return 1 [0.0006s]
        # ├── fibonacci(1)
        # │   └── return 1 [0.0000s]
        # └── return 2 [0.0008s]
    """
    if func is None:
        return functools.partial(watch, track_time=track_time, truncate_len=truncate_len,
                                 max_depth=max_depth, export_path=export_path, track_vars=track_vars)

    # ── Helpers ─────────────────────────────────────────────────

    def _get_repr(val):
        """Return a repr string for *val*, truncated to *truncate_len* characters."""
        s = repr(val)
        if truncate_len and len(s) > truncate_len:
            s = s[:truncate_len - 3] + "..."
        return s

    def _log(msg):
        """Print to console or append to file."""
        if export_path:
            try:
                with open(export_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        else:
            print(msg)

    def _prefix(depth):
        """Build the tree prefix for a child node at the given depth."""
        if depth == 0:
            return ""
        return "│   " * (depth - 1) + "├── "

    def _continuation(depth):
        """Build the continuation (vertical lines) for content at the given depth."""
        return "│   " * depth

    # ── Trace entry / exit ──────────────────────────────────────

    def _trace_call(args, kwargs, depth):
        """Print the function call line and return start_time."""
        pos_args = [_get_repr(a) for a in args]
        kw_args = [f"{k}={_get_repr(v)}" for k, v in kwargs.items()]
        all_args = ", ".join(pos_args + kw_args)
        call_str = f"{func.__name__}({all_args})"
        _log(f"{_prefix(depth)}{call_str}")
        return _time.perf_counter() if track_time else None

    def _trace_return(depth, start_time, result=None, exc=None):
        """Print the return/exception line as the last child of the call."""
        elapsed = f" [{_time.perf_counter() - start_time:.4f}s]" if (track_time and start_time) else ""
        ret_prefix = _continuation(depth) + "└── "
        if exc is not None:
            _log(f"{ret_prefix}{type(exc).__name__}: {str(exc)}{elapsed}")
        else:
            _log(f"{ret_prefix}return {_get_repr(result)}{elapsed}")

    # ── Variable state tracking (sys.settrace) ──────────────────

    def _make_var_tracer(depth):
        """Create a sys.settrace local tracer for variable state tracking."""
        var_prefix = _continuation(depth) + "│   "
        prev_locals = [None]  # None = first snapshot not yet captured
        target_code = func.__code__

        def local_tracer(frame, event, arg):
            if event == 'line':
                current = {}
                for k, v in frame.f_locals.items():
                    if k.startswith('_'):
                        continue
                    try:
                        current[k] = _get_repr(v)
                    except Exception:
                        current[k] = '<repr error>'

                if prev_locals[0] is None:
                    # First line event — capture parameters as baseline, don't log them
                    prev_locals[0] = current
                else:
                    for k, v in current.items():
                        if k not in prev_locals[0] or prev_locals[0][k] != v:
                            _log(f"{var_prefix}· {k} = {v}")
                    prev_locals[0] = current
            return local_tracer

        def global_tracer(frame, event, arg):
            if event == 'call' and frame.f_code is target_code:
                return local_tracer
            return None

        return global_tracer

    # ── Wrapper selection ───────────────────────────────────────

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not _enabled:
                return await func(*args, **kwargs)

            depth = _depth.get()
            if max_depth is not None and depth >= max_depth:
                token = _depth.set(depth + 1)
                try:
                    return await func(*args, **kwargs)
                finally:
                    _depth.reset(token)

            start_time = _trace_call(args, kwargs, depth)
            token = _depth.set(depth + 1)
            # track_vars not supported for async (sys.settrace is thread-level)
            try:
                result = await func(*args, **kwargs)
                _depth.reset(token)
                _trace_return(depth, start_time, result=result)
                return result
            except Exception as e:
                _depth.reset(token)
                _trace_return(depth, start_time, exc=e)
                raise
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not _enabled:
                return func(*args, **kwargs)

            depth = _depth.get()
            if max_depth is not None and depth >= max_depth:
                token = _depth.set(depth + 1)
                try:
                    return func(*args, **kwargs)
                finally:
                    _depth.reset(token)

            start_time = _trace_call(args, kwargs, depth)
            token = _depth.set(depth + 1)

            if track_vars:
                old_trace = _sys.gettrace()
                _sys.settrace(_make_var_tracer(depth))

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if track_vars:
                    _sys.settrace(old_trace)
                _depth.reset(token)
                _trace_return(depth, start_time, exc=e)
                raise
            else:
                if track_vars:
                    _sys.settrace(old_trace)
                _depth.reset(token)
                _trace_return(depth, start_time, result=result)
                return result
        return sync_wrapper
