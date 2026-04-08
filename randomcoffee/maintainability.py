import json
import os
import sys

"""
Program that checks the output of `radon mi -j <files>`.
"""
THRESHOLD = int(os.getenv("THRESHOLD", "25"))


failed = 0
for filename, values in json.load(sys.stdin).items():
    if values["mi"] < THRESHOLD:
        failed += 1
        print(
            f"In file {filename}: maintainability too low:",
            f"{values["mi"]} < {THRESHOLD}",
            file=sys.stderr,
        )
quit(1 if failed else 0)
