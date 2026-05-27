# TraceFlow

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

---

## Installation

```bash
pip install traceflow-py

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

> **Note:** Variable tracking uses `sys.settrace` and is only available for synchronous functions. It adds overhead and is best used for targeted debugging, not production code.

---

### 9. Keyword Arguments

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

## Configuration Reference

| Parameter | Type | Default | Description |
|---|---|---|---|
| `track_time` | `bool` | `True` | Append `[0.0042s]` execution time to each return line |
| `truncate_len` | `int` | `50` | Max characters for argument/return repr. `0` or `None` to disable |
| `max_depth` | `int` | `None` | Stop tracing beyond this call depth. `None` for unlimited |
| `export_path` | `str` | `None` | Write trace to a file instead of stdout |
| `track_vars` | `bool` | `False` | Log local variable assignments inside the function (sync only) |

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

All Rights Reserved.
