import functools
import contextvars
import inspect
import time as _time

_depth = contextvars.ContextVar('depth', default=0)

def watch(func=None, *, track_time=True, truncate_len=50, max_depth=None, export_path=None):
    if func is None:
        return functools.partial(watch, track_time=track_time, truncate_len=truncate_len, max_depth=max_depth, export_path=export_path)

    def _get_repr(val):
        s = repr(val)
        if truncate_len and len(s) > truncate_len:
            s = s[:truncate_len - 3] + "..."
        return s

    def _log(msg):
        if export_path:
            try:
                with open(export_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        else:
            print(msg)

    def _prefix(depth, is_last=False):
        """Build the tree prefix for a node at the given depth."""
        if depth == 0:
            return ""
        # For depth >= 1, the prefix is "│   " repeated (depth-1) times, then ├── or └──
        connector = "└── " if is_last else "├── "
        return "│   " * (depth - 1) + connector

    def _continuation(depth):
        """Build the continuation prefix for child lines under a node at the given depth."""
        return "│   " * depth

    def _trace_call(args, kwargs, depth):
        """Print the function call line and return start_time."""
        pos_args = [_get_repr(a) for a in args]
        kw_args = [f"{k}={_get_repr(v)}" for k, v in kwargs.items()]
        all_args = ", ".join(pos_args + kw_args)
        call_str = f"{func.__name__}({all_args})"

        prefix = _prefix(depth)
        _log(f"{prefix}{call_str}")

        return _time.perf_counter() if track_time else None

    def _trace_return(depth, start_time, result=None, exc=None):
        """Print the return/exception line as a child of the call."""
        elapsed = f" [{_time.perf_counter() - start_time:.4f}s]" if (track_time and start_time) else ""

        # The return line is always the last child: use └──
        ret_prefix = _continuation(depth) + "└── "

        if exc is not None:
            _log(f"{ret_prefix}{type(exc).__name__}: {str(exc)}{elapsed}")
        else:
            ret_str = _get_repr(result)
            _log(f"{ret_prefix}return {ret_str}{elapsed}")

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            depth = _depth.get()

            if max_depth is not None and depth >= max_depth:
                token = _depth.set(depth + 1)
                try:
                    return await func(*args, **kwargs)
                finally:
                    _depth.reset(token)

            start_time = _trace_call(args, kwargs, depth)
            token = _depth.set(depth + 1)
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
            depth = _depth.get()

            if max_depth is not None and depth >= max_depth:
                token = _depth.set(depth + 1)
                try:
                    return func(*args, **kwargs)
                finally:
                    _depth.reset(token)

            start_time = _trace_call(args, kwargs, depth)
            token = _depth.set(depth + 1)
            try:
                result = func(*args, **kwargs)
                _depth.reset(token)
                _trace_return(depth, start_time, result=result)
                return result
            except Exception as e:
                _depth.reset(token)
                _trace_return(depth, start_time, exc=e)
                raise
        return sync_wrapper
