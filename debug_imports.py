#!/usr/bin/env python3
"""Debug script to validate import path assumptions"""

import sys
import os

print("=== Import Path Debugging ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print()

# Test 1: Check if deep_research exists as a package
print("Test 1: Checking if 'deep_research' exists as installed package...")
try:
    import deep_research
    print("✓ deep_research package found")
    print(f"  Location: {deep_research.__file__}")
except ImportError as e:
    print(f"✗ deep_research package NOT found: {e}")

print()

# Test 2: Check if local orchestration_agent.tools.deep_research exists
print("Test 2: Checking local orchestration_agent.tools.deep_research...")
try:
    from orchestration_agent.tools.deep_research.config import ChatConfig
    print("✓ Local deep_research config found")
    print(f"  ChatConfig: {ChatConfig}")
except ImportError as e:
    print(f"✗ Local deep_research config NOT found: {e}")

print()

# Test 3: Check if orchestration_agent is properly structured
print("Test 3: Checking orchestration_agent package structure...")
try:
    import orchestration_agent
    print("✓ orchestration_agent package found")
except ImportError as e:
    print(f"✗ orchestration_agent package NOT found: {e}")

print()

# Test 4: List what's actually in the tools directory
print("Test 4: Listing orchestration_agent/tools/ contents...")
tools_path = "orchestration_agent/tools"
if os.path.exists(tools_path):
    for item in os.listdir(tools_path):
        item_path = os.path.join(tools_path, item)
        if os.path.isdir(item_path):
            print(f"  [DIR]  {item}")
            # Check for __init__.py
            init_file = os.path.join(item_path, "__init__.py")
            if os.path.exists(init_file):
                print(f"    ✓ Has __init__.py")
            else:
                print(f"    ✗ Missing __init__.py")
        else:
            print(f"  [FILE] {item}")
else:
    print(f"  ✗ {tools_path} directory not found")