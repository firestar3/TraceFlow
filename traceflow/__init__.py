import functools
import contextvars
import inspect
import time as _time
import reprlib

_depth = contextvars.ContextVar('depth', default=0)
_shared_pending = contextvars.ContextVar('shared_pending', default=None)

def watch(func=None, *, track_time=True, truncate_len=50, max_depth=None, export_path=None):
    if func is None:
        return functools.partial(watch, track_time=track_time, truncate_len=truncate_len, max_depth=max_depth, export_path=export_path)

    def _get_repr(val):
        s = repr(val)
        if truncate_len and len(s) > truncate_len:
            s = s[:truncate_len - 3] + "..."
        return s

    def _log_output(msg, current_export):
        if current_export:
            try:
                with open(current_export, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        else:
            print(msg)

    def _trace_before(args, kwargs):
        depth = _depth.get()
        
        should_trace = True
        if max_depth is not None and depth >= max_depth:
            should_trace = False
            
        if not should_trace:
            depth_token = _depth.set(depth + 1)
            return False, depth, None, depth_token, None, None
            
        pos_args = [_get_repr(a) for a in args]
        kw_args = [f"{k}={_get_repr(v)}" for k, v in kwargs.items()]
        all_args = ", ".join(pos_args + kw_args)
        
        call_str = f"{func.__name__}({all_args})"
        
        prefix = "│   " * (depth - 1) + "├── " if depth > 0 else ""
        full_call_str = prefix + call_str
        
        # Consume parent's pending call if any
        parent_pending = _shared_pending.get()
        if parent_pending is not None and parent_pending:
            _log_output(parent_pending.pop(), export_path)
            
        # Create our own pending call state for children
        my_pending = [full_call_str]
        pending_token = _shared_pending.set(my_pending)
        depth_token = _depth.set(depth + 1)
        
        start_time = _time.perf_counter() if track_time else None
        return True, depth, start_time, depth_token, pending_token, my_pending

    def _trace_after(should_trace, depth, start_time, depth_token, pending_token, my_pending, result=None, exc=None):
        _depth.reset(depth_token)
        
        if not should_trace:
            return
            
        _shared_pending.reset(pending_token)
            
        elapsed = f" [{_time.perf_counter() - start_time:.4f}s]" if (track_time and start_time) else ""
            
        if exc is not None:
            if my_pending:
                pending_call = my_pending.pop()
                _log_output(f"{pending_call} -> {type(exc).__name__}: {str(exc)}{elapsed}", export_path)
            else:
                ret_prefix = "│   " * depth + "└── "
                _log_output(f"{ret_prefix}{type(exc).__name__}: {str(exc)}{elapsed}", export_path)
        else:
            ret_str = _get_repr(result)
            if my_pending:
                pending_call = my_pending.pop()
                _log_output(f"{pending_call} -> {ret_str}{elapsed}", export_path)
            else:
                ret_prefix = "│   " * depth + "└── "
                _log_output(f"{ret_prefix}return {ret_str}{elapsed}", export_path)

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            should_trace, depth, start_time, depth_token, pending_token, my_pending = _trace_before(args, kwargs)
            try:
                result = await func(*args, **kwargs)
                _trace_after(should_trace, depth, start_time, depth_token, pending_token, my_pending, result=result)
                return result
            except Exception as e:
                _trace_after(should_trace, depth, start_time, depth_token, pending_token, my_pending, exc=e)
                raise
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            should_trace, depth, start_time, depth_token, pending_token, my_pending = _trace_before(args, kwargs)
            try:
                result = func(*args, **kwargs)
                _trace_after(should_trace, depth, start_time, depth_token, pending_token, my_pending, result=result)
                return result
            except Exception as e:
                _trace_after(should_trace, depth, start_time, depth_token, pending_token, my_pending, exc=e)
                raise
        return sync_wrapper
