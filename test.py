import asyncio
from traceflow import watch

# ── 1. Recursive Call Tree ──────────────────────────────────────
print("=" * 50)
print("1. RECURSIVE CALL TREE")
print("=" * 50)

@watch(track_time=True)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(3)

# ── 2. Execution Time Tracking ──────────────────────────────────
print("\n" + "=" * 50)
print("2. EXECUTION TIME TRACKING")
print("=" * 50)

@watch(track_time=True)
def slow_add(a, b):
    import time
    time.sleep(0.05)
    return a + b

slow_add(10, 20)

# ── 3. Argument & Return Truncation ────────────────────────────
print("\n" + "=" * 50)
print("3. TRUNCATION (truncate_len=30)")
print("=" * 50)

@watch(truncate_len=30)
def process_large_data(data):
    return [x * 2 for x in data]

process_large_data(list(range(50)))

# ── 4. Exception Tracing ───────────────────────────────────────
print("\n" + "=" * 50)
print("4. EXCEPTION TRACING")
print("=" * 50)

@watch()
def divide(a, b):
    return a / b

@watch()
def safe_math(x, y):
    return divide(x, y)

try:
    safe_math(10, 0)
except ZeroDivisionError:
    pass  # Exception is traced in the tree

# ── 5. Max Depth Limiting ──────────────────────────────────────
print("\n" + "=" * 50)
print("5. MAX DEPTH (max_depth=2)")
print("=" * 50)

@watch(max_depth=2)
def deep_fib(n):
    if n <= 1:
        return n
    return deep_fib(n - 1) + deep_fib(n - 2)

deep_fib(4)

# ── 6. Async Concurrency ──────────────────────────────────────
print("\n" + "=" * 50)
print("6. ASYNC CONCURRENCY")
print("=" * 50)

@watch()
async def fetch_data(id):
    await asyncio.sleep(0.01)
    return f"data_{id}"

@watch()
async def fetch_all():
    return await asyncio.gather(fetch_data(1), fetch_data(2), fetch_data(3))

asyncio.run(fetch_all())

# ── 7. File Export ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("7. FILE EXPORT (trace_output.txt)")
print("=" * 50)

@watch(export_path="trace_output.txt")
def exported_fib(n):
    if n <= 1:
        return n
    return exported_fib(n - 1) + exported_fib(n - 2)

exported_fib(3)
print("  -> Trace written to trace_output.txt")

# ── 8. Keyword Arguments ──────────────────────────────────────
print("\n" + "=" * 50)
print("8. KEYWORD ARGUMENTS")
print("=" * 50)

@watch()
def greet(name, greeting="Hello", punctuation="!"):
    return f"{greeting}, {name}{punctuation}"

greet("Aarav", greeting="Hey", punctuation="!!")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETE")
print("=" * 50)