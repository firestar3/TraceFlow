import asyncio
import traceflow
from traceflow import watch

# ── 1. Recursive Call Tree ──────────────────────────────────────
print("=" * 55)
print("  1. RECURSIVE CALL TREE")
print("=" * 55)

@watch(track_time=True)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibonacci(3)

# ── 2. Execution Time Tracking ──────────────────────────────────
print("\n" + "=" * 55)
print("  2. EXECUTION TIME TRACKING")
print("=" * 55)

@watch(track_time=True)
def slow_add(a, b):
    import time
    time.sleep(0.05)
    return a + b

slow_add(10, 20)

# ── 3. Argument & Return Truncation ────────────────────────────
print("\n" + "=" * 55)
print("  3. TRUNCATION (truncate_len=30)")
print("=" * 55)

@watch(truncate_len=30)
def process_large_data(data):
    return [x * 2 for x in data]

process_large_data(list(range(50)))

# ── 4. Exception Tracing ───────────────────────────────────────
print("\n" + "=" * 55)
print("  4. EXCEPTION TRACING")
print("=" * 55)

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
print("\n" + "=" * 55)
print("  5. MAX DEPTH (max_depth=2)")
print("=" * 55)

@watch(max_depth=2)
def deep_fib(n):
    if n <= 1:
        return n
    return deep_fib(n - 1) + deep_fib(n - 2)

deep_fib(4)

# ── 6. Async Concurrency ──────────────────────────────────────
print("\n" + "=" * 55)
print("  6. ASYNC CONCURRENCY")
print("=" * 55)

@watch()
async def fetch_data(id):
    await asyncio.sleep(0.01)
    return f"data_{id}"

@watch()
async def fetch_all():
    return await asyncio.gather(fetch_data(1), fetch_data(2), fetch_data(3))

asyncio.run(fetch_all())

# ── 7. File Export ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("  7. FILE EXPORT (trace_output.txt)")
print("=" * 55)

@watch(export_path="trace_output.txt")
def exported_fib(n):
    if n <= 1:
        return n
    return exported_fib(n - 1) + exported_fib(n - 2)

exported_fib(3)
print("  -> Trace written to trace_output.txt")

# ── 8. Keyword Arguments ──────────────────────────────────────
print("\n" + "=" * 55)
print("  8. KEYWORD ARGUMENTS")
print("=" * 55)

@watch()
def greet(name, greeting="Hello", punctuation="!"):
    return f"{greeting}, {name}{punctuation}"

greet("Aarav", greeting="Hey", punctuation="!!")

# ── 9. Global Enable / Disable ────────────────────────────────
print("\n" + "=" * 55)
print("  9. GLOBAL ENABLE / DISABLE")
print("=" * 55)

@watch()
def add(a, b):
    return a + b

print("  [traceflow enabled — trace visible]")
add(1, 2)

traceflow.disable()
print("\n  [traceflow disabled — no trace]")
result = add(3, 4)
print(f"  add(3, 4) still returned {result}, just no trace output")

traceflow.enable()
print("\n  [traceflow re-enabled — trace visible again]")
add(5, 6)

# ── 10. Variable State Tracking ───────────────────────────────
print("\n" + "=" * 55)
print("  10. VARIABLE STATE TRACKING")
print("=" * 55)

@watch(track_vars=True)
def compute(x, y):
    total = x + y
    doubled = total * 2
    message = f"Result: {doubled}"
    return doubled

compute(5, 3)

print("\n  --- Variable tracking with a loop ---")

@watch(track_vars=True, truncate_len=80)
def sum_list(items):
    total = 0
    for val in items:
        total += val
    return total

sum_list([10, 20, 30])

print("\n" + "=" * 55)
print("  ALL TESTS COMPLETE")
print("=" * 55)