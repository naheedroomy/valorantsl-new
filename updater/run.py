#!/usr/bin/env python3
"""
Simple runner script for the ValorantSL Player Updater Service
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from updater
sys.path.append(str(Path(__file__).parent.parent))

# Import directly from the main module
from main import main

if __name__ == "__main__":
    main()