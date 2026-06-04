# TraceFlow

![Downloads](https://img.shields.io/badge/non--mirrored_downloads-1,600+-2K2021?labelColor=22c55e&logo=pypi&logoColor=white)

**TraceFlow** is a lightweight, zero-dependency Python decorator library for visually tracing function execution. It renders beautiful, indented call trees directly to your console — making debugging recursive, nested, and async code effortless.

```
fibonacci(3)
├── fibonacci(2)
│   ├── fibonacci(1)
│   │   └── return 1 [0.0003s]
│   ├── fibonacci(0)
│   │   └── return 0 [0.0000s]
│   └── return 1 [0.0006s]
├── fibonacci(1)
│   └── return 1 [0.0000s]
└── return 2 [0.0008s]
```

---

## Features

| Feature | Description |
|---|---|
| **Call Trees** | Nested, indented tree visualization for every function call |
| **Execution Time** | Per-call timing with `[0.0042s]` annotations |
| **Truncation** | Smart character-limit truncation for large arguments and returns |
| **Exception Tracing** | Captures and renders exceptions inline in the call tree |
| **Async Support** | Safely traces `async`/`await` functions and `asyncio.gather` |
| **Depth Limiting** | Cap tracing depth with `max_depth` to reduce noise |
| **File Export** | Redirect trace output to a file instead of the console |
| **Global Toggle** | `traceflow.disable()` / `traceflow.enable()` to control all tracing at runtime |
| **Variable Tracking** | `track_vars=True` to log every local variable assignment inside a function |
| **Selective Variables** | `track_vars=['x', 'y']` to track only specific variables by name |
| **Capture Prints** | `capture_prints=True` to intercept `print()` calls and log them inline in the tree |
| **Memory Profiling** | `track_memory=True` to append `[+1.2000 MB]` memory allocation to the return line |
| **Python Logging** | `logger=my_logger` to emit trace lines through the standard `logging` module |
| **Data Masking** | `mask_args=['password']` and `track_return=False` to hide sensitive data in traces |
| **Return Assertions** | `assert_return=lambda x: x > 0` to log warnings for invalid returns |
| **JSON Export** | `export_json=True` to output structured JSON logs instead of text trees |
| **Multi-Threading** | `thread_safe=True` to buffer output and prevent interleaving |
| **Class Decorator** | `@watch_class` to automatically wrap all methods in a class |
| **Context Manager** | `with traceflow.watch_block("name"):` to trace arbitrary code blocks |

---

## Installation

```bash
pip install traceflow-py
```

---

## Quick Start

```python
from traceflow import watch

@watch()
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(3)
```

**Output:**
```
fibonacci(3)
├── fibonacci(2)
│   ├── fibonacci(1)
│   │   └── return 1 [0.0003s]
│   ├── fibonacci(0)
│   │   └── return 0 [0.0000s]
│   └── return 1 [0.0006s]
├── fibonacci(1)
│   └── return 1 [0.0000s]
└── return 2 [0.0008s]
```

---

## Feature Guide

### 1. Execution Time Tracking

Every traced call automatically measures wall-clock time.

```python
from traceflow import watch
import time

@watch(track_time=True)
def slow_add(a, b):
    time.sleep(0.05)
    return a + b

slow_add(10, 20)
```

```
slow_add(10, 20)
└── return 30 [0.0502s]
```

Set `track_time=False` to disable timing:

```python
@watch(track_time=False)
def add(a, b):
    return a + b

add(1, 2)
```

```
add(1, 2)
└── return 3
```

---

### 2. Argument & Return Truncation

Prevent massive data structures from flooding your console with `truncate_len`.

```python
@watch(truncate_len=30)
def process(data):
    return [x * 2 for x in data]

process(list(range(50)))
```

```
process([0, 1, 2, 3, 4, 5, 6, 7, 8,...)
└── return [0, 2, 4, 6, 8, 10, 12, 14,... [0.0000s]
```

The character limit applies to both arguments and return values. Set `truncate_len=None` or `truncate_len=0` to disable truncation entirely.

---

### 3. Exception Tracing

Exceptions are captured, rendered in the tree, and re-raised — so your error handling works normally while you get full visibility.

```python
@watch()
def divide(a, b):
    return a / b

@watch()
def safe_math(x, y):
    return divide(x, y)

try:
    safe_math(10, 0)
except ZeroDivisionError:
    pass
```

```
safe_math(10, 0)
├── divide(10, 0)
│   └── ZeroDivisionError: division by zero [0.0000s]
└── ZeroDivisionError: division by zero [0.0000s]
```

The exception propagates through each level of the call tree, showing exactly where it originated and how it bubbled up.

---

### 4. Max Depth Limiting

Reduce noise in deeply recursive functions by capping the trace depth.

```python
@watch(max_depth=2)
def deep_fib(n):
    if n <= 1:
        return n
    return deep_fib(n - 1) + deep_fib(n - 2)

deep_fib(4)
```

```
deep_fib(4)
├── deep_fib(3)
│   └── return 2 [0.0000s]
├── deep_fib(2)
│   └── return 1 [0.0000s]
└── return 3 [0.0000s]
```

Calls beyond `max_depth` still execute normally — they just aren't traced.

---

### 5. Async Function Support

TraceFlow natively supports `async` functions. Concurrent tasks from `asyncio.gather` are traced cleanly.

```python
import asyncio
from traceflow import watch

@watch()
async def fetch_data(id):
    await asyncio.sleep(0.01)
    return f"data_{id}"

@watch()
async def fetch_all():
    return await asyncio.gather(fetch_data(1), fetch_data(2), fetch_data(3))

asyncio.run(fetch_all())
```

```
fetch_all()
├── fetch_data(1)
│   └── return 'data_1' [0.0123s]
├── fetch_data(2)
│   └── return 'data_2' [0.0123s]
├── fetch_data(3)
│   └── return 'data_3' [0.0123s]
└── return ['data_1', 'data_2', 'data_3'] [0.0126s]
```

---

### 6. File Export

Redirect all trace output to a text file instead of the console.

```python
@watch(export_path="trace_output.txt")
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(3)
# -> Trace written to trace_output.txt
```

The file is appended to, so multiple runs accumulate in the same file.

---

### 7. Global Enable / Disable

Turn all tracing on or off at runtime without removing decorators. Functions still execute normally when tracing is disabled — only the output is suppressed.

```python
import traceflow
from traceflow import watch

@watch()
def add(a, b):
    return a + b

add(1, 2)           # Trace is printed

traceflow.disable()
add(3, 4)           # No trace output, but returns 7 normally

traceflow.enable()
add(5, 6)           # Trace resumes
```

```
add(1, 2)
└── return 3 [0.0000s]

add(5, 6)
└── return 11 [0.0000s]
```

Also available: `traceflow.is_enabled()` to check current state.

---

### 8. Variable State Tracking

See exactly how local variables change inside a function, line by line. Parameters are captured as a baseline and not logged (they're already visible in the call signature).

```python
@watch(track_vars=True)
def compute(x, y):
    total = x + y
    doubled = total * 2
    message = f"Result: {doubled}"
    return doubled

compute(5, 3)
```

```
compute(5, 3)
│   · total = 8
│   · doubled = 16
│   · message = 'Result: 16'
└── return 16 [0.0002s]
```

Variable tracking inside a loop:

```python
@watch(track_vars=True)
def sum_list(items):
    total = 0
    for val in items:
        total += val
    return total

sum_list([10, 20, 30])
```

```
sum_list([10, 20, 30])
│   · total = 0
│   · val = 10
│   · total = 10
│   · val = 20
│   · total = 30
│   · val = 30
│   · total = 60
└── return 60 [0.0001s]
```

> **Note:** Variable tracking adds overhead and is best used for targeted debugging, not production code. TraceFlow cleanly supports variable tracking in **both synchronous and asynchronous (`async`/`await`) functions**, even under heavy concurrency.

#### Selective Variable Tracking

If you only care about specific variables, pass a list of names instead of `True`. All other locals will be ignored.

```python
@watch(track_vars=['total', 'doubled'])
def compute(x, y):
    total = x + y
    doubled = total * 2
    message = f'Result: {doubled}'
    return doubled

compute(5, 3)
```

```
compute(5, 3)
│   · total = 8
│   · doubled = 16
└── return 16 [0.0003s]
```

Notice that `message` is not logged because it was not in the filter list.

---

### 9. Capture Prints (Console Interception)

If your function contains standard `print()` statements, they normally break the trace tree formatting. By enabling `capture_prints=True`, TraceFlow will temporarily hijack `sys.stdout` and inject your print statements directly into the tree hierarchy.

```python
@watch(capture_prints=True)
def process_data():
    print("Loading data...")
    print("Processing...")
    return True

process_data()
```

```
process_data()
│   · print: Loading data...
│   · print: Processing...
└── return True [0.0000s]
```

---

### 10. Python `logging` Integration

For enterprise applications that require all output to be routed through standard logging channels instead of `sys.stdout`, you can pass a standard Python `logger` to the decorator. You can optionally specify the `log_level` (it defaults to `logging.DEBUG`).

```python
import logging
from traceflow import watch

logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

@watch(logger=logger, log_level=logging.INFO)
def authenticate_user(user_id):
    return True

authenticate_user(42)
```

```
INFO:my_app:authenticate_user(42)
INFO:my_app:└── return True [0.0102s]
```

---

### 11. Memory Profiling

Leverage Python's built-in `tracemalloc` to track the memory allocated during the execution of your function. TraceFlow will append the memory delta directly to the return line.

```python
@watch(track_memory=True)
def load_large_dataset():
    return [x for x in range(10000)]

load_large_dataset()
```

```
load_large_dataset()
└── return [0, 1, 2, 3, ... [0.0026s] [+0.3786 MB]
```

---

### 12. Class-Level Decorator (`@watch_class`)

Instead of manually decorating every single method, you can use `@watch_class` to automatically apply the `@watch` logic to all methods (including `__init__`, while safely ignoring other magic dunder methods). It accepts all the same configuration arguments as `@watch`.

```python
from traceflow import watch_class

@watch_class(track_time=False)
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return self._transform(self.data)

    def _transform(self, data):
        return [x * 2 for x in data]

processor = DataProcessor([1, 2, 3])
processor.process()
```

```
__init__(<__main__.DataProcessor object at ...>, [1, 2, 3])
└── return None
process(<__main__.DataProcessor object at ...>)
├── _transform(<__main__.DataProcessor object at ...>, [1, 2, 3])
│   └── return [2, 4, 6]
└── return [2, 4, 6]
```

---

### 13. Keyword Arguments

TraceFlow displays both positional and keyword arguments.

```python
@watch()
def greet(name, greeting="Hello", punctuation="!"):
    return f"{greeting}, {name}{punctuation}"

greet("Aarav", greeting="Hey", punctuation="!!")
```

```
greet('Aarav', greeting='Hey', punctuation='!!')
└── return 'Hey, Aarav!!' [0.0000s]
```

---

### 14. Data Masking (Security)

When tracing functions that handle sensitive data like passwords or API keys, you can prevent them from leaking into the trace logs.

* `mask_args`: Pass a list of argument names. Their values will be replaced with `'***'`.
* `track_return`: Set to `False` to hide the return value.

```python
@watch(mask_args=['password', 'secret_key'], track_return=False)
def login(username, password, secret_key=None):
    return "session_token_123"

login("aarav", "my_super_secret_pass", secret_key="456789")
```

```
login(username='aarav', password='***', secret_key='***')
└── return <hidden> [0.0001s]
```

---

### 15. Return Assertions (`assert_return`)

You can pass a callable to `assert_return` to automatically validate the output of your function. If the callable returns `False` or raises an exception, TraceFlow will prominently inject a `[WARNING]` into the trace tree.

```python
@watch(assert_return=lambda x: x > 0)
def process_positive_only(val):
    return val

process_positive_only(-5)
```

```
process_positive_only(val=-5)
│   · [WARNING] assert_return failed
└── return -5 [0.0000s]
```

---

### 16. Context Manager (`watch_block`)

Sometimes you want to trace an arbitrary block of code rather than a single function. The `watch_block` context manager creates a named node in the call tree and supports nesting, timing, `capture_prints`, and `track_memory`.

```python
from traceflow import watch_block

with watch_block("Main Pipeline"):
    with watch_block("Step 1: Load Data"):
        data = load_data()
    with watch_block("Step 2: Process"):
        result = process(data)
```

```
Main Pipeline
├── Step 1: Load Data
│   └── done [0.0001s]
├── Step 2: Process
│   └── done [0.0002s]
└── done [0.0005s]
```

You can also capture prints inside a block:

```python
with watch_block("Print Test", capture_prints=True):
    print("Hello from inside a block!")
```

```
Print Test
│   · print: Hello from inside a block!
└── done [0.0001s]
```

---

### 17. JSON Export (Observability)

By default, TraceFlow prints visual text trees. If you want to integrate with observability tools like ELK, DataDog, or custom log parsers, you can enable `export_json=True`. This converts the output into structured JSON Lines (JSONL). 

```python
@watch(export_json=True)
def parse_data(item_id, debug=False):
    if not debug:
        return {"status": "ok"}
    raise ValueError("Debug failed")

parse_data(42)
```

```json
{"name": "parse_data", "depth": 0, "timestamp": "2026-06-03T22:18:19.322+00:00", "thread_id": 16076, "args": {"item_id": "42", "debug": "False"}, "duration_ms": 229.4, "return": "{'status': 'ok'}"}
```

---

### 18. Multi-Threading Support

TraceFlow natively handles `asyncio` concurrency seamlessly. However, if you use standard Python threading (e.g., `ThreadPoolExecutor`), multiple threads printing to `stdout` at the same time can cause interleaved text.

To fix this, pass `thread_safe=True`. TraceFlow will use `contextvars` to buffer the entire call tree in memory for that specific thread, and only print it atomically once the root function completes.

```python
import concurrent.futures
from traceflow import watch

@watch(thread_safe=True)
def threaded_worker(worker_id):
    return f"Worker {worker_id} done"

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(threaded_worker, i) for i in range(3)]
```

---

## Configuration Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track_time` | `bool` | `True` | Append `[0.0042s]` execution time to each return line |
| `truncate_len` | `int` | `50` | Max characters for argument/return repr. `0` or `None` to disable |
| `max_depth` | `int` | `None` | Stop tracing beyond this call depth. `None` for unlimited |
| `export_path` | `str` | `None` | Write trace to a file instead of stdout |
| `track_vars` | `bool` or `list` | `False` | `True` for all variables, or a list of names like `['x', 'y']` |
| `capture_prints` | `bool` | `False` | Intercept `print()` calls and log them inline in the tree |
| `track_memory` | `bool` | `False` | Track memory allocation delta and append to return line |
| `logger` | `logging.Logger` | `None` | A standard Python logger to emit trace lines to |
| `log_level` | `int` | `logging.DEBUG` | The logging level to use if `logger` is provided |
| `mask_args` | `list` | `None` | List of argument names to replace with `'***'` in trace |
| `track_return` | `bool` | `True` | Set to `False` to log `<hidden>` instead of the actual return value |
| `assert_return` | `callable` | `None` | Function to validate the return value. Logs a `[WARNING]` if it fails |
| `export_json` | `bool` | `False` | Outputs structured JSON logs instead of visual text trees |
| `thread_safe` | `bool` | `False` | Buffers output per-thread and prints atomically to prevent interleaving |

### Global Functions

| Function | Description |
|---|---|
| `traceflow.enable()` | Enable all tracing (default state) |
| `traceflow.disable()` | Disable all tracing — decorated functions still run normally |
| `traceflow.is_enabled()` | Returns `True` if tracing is currently active |

---

## Author

**Aarav Agarwal**

## License

This project is licensed under the [MIT License](LICENSE).
