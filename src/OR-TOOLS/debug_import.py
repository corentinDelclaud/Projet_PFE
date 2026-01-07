import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import enum
    print(f"Enum module: {enum}")
    from classes.jour_preference import jour_pref
    print("Successfully imported jour_pref")
except Exception as e:
    print(f"Error: {e}")
