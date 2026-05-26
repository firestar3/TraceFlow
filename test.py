import asyncio
from traceflow import watch

print("=== 1. Basic Tree & Execution Time ===")
# By default, @watch tracks both the call tree and the time it takes.
@watch(track_time=True)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

fibonacci(4)


print("\n=== 2. Argument & Return Truncation ===")
# Use truncate_len to prevent huge lists or strings from spamming your console.
@watch(truncate_len=100, track_time = True)
def process_large_data(data):
    return [x * 2 for x in data]

process_large_data(list(range(100)))  # Will cleanly truncate the 100 items


print("\n=== 3. Exception Tracing ===")
# TraceFlow catches exceptions, prints them in the tree, and safely re-raises them.
@watch()
def divide(a, b):
    return a / b

@watch()
def calculate_math():
    return divide(10, 0)

try:
    calculate_math()
except ZeroDivisionError:
    pass # Caught just to let the script continue


print("\n=== 4. Max Depth Limiting ===")
# Useful for huge codebases where you only want to trace the top few layers.
@watch(max_depth=3)
def deep_recursion(n):
    if n == 0:
        return "done"
    return deep_recursion(n-1)

deep_recursion(5)


print("\n=== 5. Async / Await Concurrency ===")
# TraceFlow natively supports async and asyncio.gather without mangling the tree!
@watch()
async def fetch_data(user_id):
    await asyncio.sleep(0.01)
    return f"data_for_{user_id}"

@watch()
async def fetch_all_users():
    return await asyncio.gather(fetch_data(1), fetch_data(2))

asyncio.run(fetch_all_users())


print("\n=== 6. File Export ===")
# Want to save the trace to a file instead of just your console?
@watch(export_path="trace_output.txt")
def secret_computation(x):
    return x * 42

secret_computation(10)
print("Check 'trace_output.txt' in your folder for the output!")