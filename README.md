# TraceFlow

TraceFlow is a lightweight, powerful Python decorator library for visually tracing function calls, arguments, return values, execution times, and exceptions. It prints a beautiful, indented call tree directly to your console or to a file, making debugging complex or recursive code effortless.

## Features

- **Nested Call Trees**: Easily visualize deeply nested or recursive function calls.
- **Execution Time**: Automatically measures how long each function takes to execute.
- **Async Concurrency**: Safely traces `async` functions (even concurrent `asyncio.gather` tasks) without jumbling the output.
- **Smart Truncation**: Prevents massive lists or strings from flooding your console by defining a strict character limit.
- **Exception Tracing**: Catches, renders, and re-raises exceptions seamlessly within the tree structure.
- **File Export**: Direct all your tracing output to a text file.

## Installation

Since TraceFlow uses modern `pyproject.toml` packaging, you can install it locally:

```bash
pip install .
```

Or just drop the `traceflow` folder into your project!

## Usage

Simply import `@watch` and decorate the functions you want to trace.

### Basic Example

```python
from traceflow import watch

@watch(track_time=True)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fibonacci(3)
```

**Output:**
```text
fibonacci(3)
├── fibonacci(2)
│   ├── fibonacci(1) -> 1 [0.0000s]
│   ├── fibonacci(0) -> 0 [0.0000s]
│   └── return 1 [0.0001s]
├── fibonacci(1) -> 1 [0.0000s]
└── return 2 [0.0001s]
```

### Argument & Return Truncation

Use `truncate_len` to prevent huge lists or strings from spamming your console.

```python
@watch(truncate_len=30)
def process_large_data(data):
    return [x * 2 for x in data]

process_large_data(list(range(100)))
# Output: process_large_data([0, 1, 2, 3...) -> [0, 2, 4, 6... [0.0000s]
```

### Async Function Support

TraceFlow natively supports async code, intelligently handling the context to keep branches cleanly separated even during concurrent execution!

```python
import asyncio
from traceflow import watch

@watch()
async def fetch_data(id):
    await asyncio.sleep(0.01)
    return f"data_{id}"

@watch()
async def fetch_all():
    return await asyncio.gather(fetch_data(1), fetch_data(2))

asyncio.run(fetch_all())
```

**Output:**
```text
fetch_all()
├── fetch_data(1) -> 'data_1' [0.0108s]
├── fetch_data(2) -> 'data_2' [0.0108s]
└── return ['data_1', 'data_2'] [0.0110s]
```

## Configuration Options

The `@watch` decorator accepts several optional parameters:
* `track_time` (bool): Defaults to `True`. Appends execution time to the end of the trace.
* `truncate_len` (int): Limit the number of characters printed for arguments and return values.
* `max_depth` (int): Stop tracing once the call stack reaches this depth.
* `export_path` (str): Output the trace to a specified file instead of standard out.

## License

All Rights Reserved.
