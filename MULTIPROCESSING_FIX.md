# Multiple Process Spawning Issue - Fixed

## Problem
When running the app with `--voice`, multiple Python processes were being spawned (7+ instances), each playing the greeting "Hi Reza, I am ready. What should we do?" multiple times.

## Root Cause
On ARM-based systems (NVIDIA Jetson Xavier), Python's multiprocessing module defaults to **"spawn"** context instead of **"fork"**:

- **"fork"**: Creates child process by copying parent, code doesn't re-execute (Linux default)
- **"spawn"**: Creates child process from scratch, re-executes all module-level code (Windows/macOS/ARM default)

When multiprocessing context is "spawn":
1. Main script starts: calls `main()` → creates orchestrator → creates pygame animation process
2. Animation process starts: imports entire module again
3. Module re-execution triggers: `if __name__ == "__main__"` check FAILS in child process
4. Each nested import/spawn creates another process, leading to exponential growth

This is especially problematic on Jetson because ARM Linux systems sometimes default to spawn context.

## Solution
Added multiprocessing context configuration in `main.py`:

```python
# Set multiprocessing to use 'fork' on systems that support it
# This prevents module re-execution on ARM/Jetson
if multiprocessing.get_start_method(allow_none=True) != 'fork':
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        # Already set, or system doesn't support fork
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except:
            pass  # Use system default
```

## Files Modified
- `src/robot_sync_app/main.py`: Added multiprocessing context setup at module level (before any Process creation)

## Result
✅ Single process only (main script + one animation subprocess)
✅ Greeting plays once at startup
✅ Desktop properly shown after app closes
