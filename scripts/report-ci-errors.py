#!/usr/bin/env python3
"""Expose bounded build/test diagnostics as GitHub annotations, preserving logs."""
from pathlib import Path
import re
import sys


def escape(value):
    return value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main():
    path = Path(sys.argv[1])
    title = sys.argv[2] if len(sys.argv) > 2 else 'Build or test failure'
    lines = path.read_text(errors='replace').splitlines()
    # Compiler and XCTest diagnostic lines carry the actual cause, unlike the
    # final generic "Process completed with exit code" annotation.
    errors = [line for line in lines if re.search(r'\berror:|Fatal error:|XCTAssert|Assertion failed|failed \(', line)]
    if not errors:
        errors = [line for line in lines if line.strip()][-10:]
    for line in errors[:12]:
        print(f'::error title={escape(title)}::{escape(line[:1600])}')


if __name__ == '__main__':
    main()
