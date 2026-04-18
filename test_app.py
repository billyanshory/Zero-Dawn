import sys
import eventlet
eventlet.monkey_patch()
try:
    import slb
    print("Application loaded successfully")
except Exception as e:
    print(f"Error loading application: {e}")
    sys.exit(1)
