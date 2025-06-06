#!/usr/bin/env python3
"""
Debug the extraction error
"""

import asyncio
import os
from src.extraction.engine import ShelfStructure

# Test what's happening
print("Testing extraction issue...")

# Check if ShelfStructure is properly imported
print(f"ShelfStructure: {ShelfStructure}")
print(f"ShelfStructure.__name__: {ShelfStructure.__name__}")

# Check what the visual system is passing
from src.systems.custom_consensus_visual import CustomConsensusVisualSystem

print("\nChecking what CustomConsensusVisualSystem is doing...")

# Look at the source
import inspect
lines = inspect.getsource(CustomConsensusVisualSystem._process_stage_with_model)
print("Method source:")
print(lines[:500])