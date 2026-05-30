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
import tracemalloc as _tracemalloc

# ── Global State ────────────────────────────────────────────────

_depth = contextvars.ContextVar('depth', default=0)
_enabled = True

_print_capturer_active = contextvars.ContextVar('print_capturer_active', default=None)
_log_buffer = contextvars.ContextVar('log_buffer', default=None)

class _MultiplexingStdout:
    def __init__(self, original_stdout):
        self._original = original_stdout
        self._buffer = contextvars.ContextVar('stdout_buffer', default="")

    def write(self, text):
        active = _print_capturer_active.get()
        if active is None:
            self._original.write(text)
            return

        _print_capturer_active.set(None)
        try:
            log_func, prefix = active
            buf = self._buffer.get() + text
            if '\n' in buf:
                lines = buf.split('\n')
                for line in lines[:-1]:
                    log_func(f"{prefix}· print: {line}")
                self._buffer.set(lines[-1])
            else:
                self._buffer.set(buf)
        finally:
            _print_capturer_active.set(active)

    def flush(self):
        active = _print_capturer_active.get()
        if active is None:
            self._original.flush()
            return
        
        _print_capturer_active.set(None)
        try:
            buf = self._buffer.get()
            if buf:
                log_func, prefix = active
                log_func(f"{prefix}· print: {buf}")
                self._buffer.set("")
        finally:
            _print_capturer_active.set(active)

    def __getattr__(self, name):
        return getattr(self._original, name)

_original_stdout = None

def _ensure_stdout_hook():
    global _original_stdout
    if _original_stdout is None:
        _original_stdout = _sys.stdout
        _sys.stdout = _MultiplexingStdout(_original_stdout)


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

def watch(func=None, *, track_time=True, truncate_len=50, max_depth=None, export_path=None, track_vars=False, capture_prints=False, track_memory=False, logger=None, log_level=None):
    """
    Decorator that traces function calls, producing an indented call tree.

    Args:
        track_time (bool): Append execution time to each return line. Default True.
        truncate_len (int): Max characters for argument/return repr. 0 or None to disable.
        max_depth (int): Stop tracing beyond this call depth. None for unlimited.
        export_path (str): Write trace output to this file instead of stdout.
        track_vars (bool): Log local variable assignments inside the function (sync only).
        capture_prints (bool): Intercept print() calls and log them inline in the tree.
        track_memory (bool): Track memory allocation delta and append to return line.
        logger (logging.Logger): A standard Python logger to emit trace lines to.
        log_level (int): The logging level to use (e.g., logging.DEBUG). Defaults to DEBUG if logger is provided.

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
                                 max_depth=max_depth, export_path=export_path, 
                                 track_vars=track_vars, capture_prints=capture_prints, 
                                 track_memory=track_memory, logger=logger, log_level=log_level)

    # ── Helpers ─────────────────────────────────────────────────

    def _get_repr(val):
        """Return a repr string for *val*, truncated to *truncate_len* characters."""
        s = repr(val)
        if truncate_len and len(s) > truncate_len:
            s = s[:truncate_len - 3] + "..."
        return s

    def _actual_log(msg):
        """Print to console, append to file, or send to Python logger."""
        if logger is not None:
            import logging
            level = log_level if log_level is not None else logging.DEBUG
            logger.log(level, msg)
        elif export_path:
            try:
                with open(export_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        else:
            print(msg)

    def _log(msg):
        """Append to the current async buffer or log immediately."""
        buf = _log_buffer.get()
        if buf is not None:
            buf.append((_actual_log, msg))
        else:
            _actual_log(msg)

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

    def _trace_return(depth, start_time, result=None, exc=None, mem_diff=None):
        """Print the return/exception line as the last child of the call."""
        elapsed = f" [{_time.perf_counter() - start_time:.4f}s]" if (track_time and start_time) else ""
        
        mem_str = ""
        if mem_diff is not None:
            if mem_diff >= 0:
                mem_str = f" [+{mem_diff / 1024 / 1024:.4f} MB]"
            else:
                mem_str = f" [{mem_diff / 1024 / 1024:.4f} MB]"

        ret_prefix = _continuation(depth) + "└── "
        if exc is not None:
            _log(f"{ret_prefix}{type(exc).__name__}: {str(exc)}{elapsed}{mem_str}")
        else:
            _log(f"{ret_prefix}return {_get_repr(result)}{elapsed}{mem_str}")

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

            # Create a localized buffer to prevent interleaved logs in concurrent async tasks
            my_buffer = []
            old_buffer = _log_buffer.get()
            buffer_token = _log_buffer.set(my_buffer)

            start_time = _trace_call(args, kwargs, depth)
            token = _depth.set(depth + 1)
            
            print_token = None
            if capture_prints:
                _ensure_stdout_hook()
                print_token = _print_capturer_active.set((_log, _continuation(depth) + "│   "))
                
            mem_start = None
            if track_memory:
                if not _tracemalloc.is_tracing():
                    _tracemalloc.start()
                mem_start = _tracemalloc.get_traced_memory()[0]

            # track_vars not supported for async (sys.settrace is thread-level)
            try:
                result = await func(*args, **kwargs)
                mem_diff = _tracemalloc.get_traced_memory()[0] - mem_start if track_memory and mem_start is not None else None
                if print_token:
                    _print_capturer_active.reset(print_token)
                _depth.reset(token)
                _trace_return(depth, start_time, result=result, mem_diff=mem_diff)
                return result
            except Exception as e:
                mem_diff = _tracemalloc.get_traced_memory()[0] - mem_start if track_memory and mem_start is not None else None
                if print_token:
                    _print_capturer_active.reset(print_token)
                _depth.reset(token)
                _trace_return(depth, start_time, exc=e, mem_diff=mem_diff)
                raise
            finally:
                _log_buffer.reset(buffer_token)
                if old_buffer is not None:
                    old_buffer.extend(my_buffer)
                else:
                    for log_func, msg in my_buffer:
                        log_func(msg)
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

            print_token = None
            if capture_prints:
                _ensure_stdout_hook()
                print_token = _print_capturer_active.set((_log, _continuation(depth) + "│   "))

            mem_start = None
            if track_memory:
                if not _tracemalloc.is_tracing():
                    _tracemalloc.start()
                mem_start = _tracemalloc.get_traced_memory()[0]

            if track_vars:
                old_trace = _sys.gettrace()
                _sys.settrace(_make_var_tracer(depth))

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if track_vars:
                    _sys.settrace(old_trace)
                mem_diff = _tracemalloc.get_traced_memory()[0] - mem_start if track_memory and mem_start is not None else None
                if print_token:
                    _print_capturer_active.reset(print_token)
                _depth.reset(token)
                _trace_return(depth, start_time, exc=e, mem_diff=mem_diff)
                raise
            else:
                if track_vars:
                    _sys.settrace(old_trace)
                mem_diff = _tracemalloc.get_traced_memory()[0] - mem_start if track_memory and mem_start is not None else None
                if print_token:
                    _print_capturer_active.reset(print_token)
                _depth.reset(token)
                _trace_return(depth, start_time, result=result, mem_diff=mem_diff)
                return result
        return sync_wrapper

def watch_class(*args, **kwargs):
    """
    Class decorator that automatically applies @watch to all methods 
    (including __init__ and properties, excluding other dunder methods).
    Accepts the same arguments as @watch.
    """
    def decorator(cls):
        for name, method in inspect.getmembers(cls):
            if inspect.isroutine(method) and (not name.startswith('__') or name == '__init__'):
                setattr(cls, name, watch(*args, **kwargs)(method))
        return cls
    return decorator
