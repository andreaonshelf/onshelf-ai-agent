#!/usr/bin/env python3
"""
Add debug logging to find the exact error
"""

import os

# Read the extraction engine file
with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/extraction/engine.py', 'r') as f:
    content = f.read()

# Add debug logging before the openai create call
debug_line = '''
            logger.info(f"DEBUG: About to call openai with output_schema={output_schema}, api_model={api_model}")
            logger.info(f"DEBUG: self.openai_client type: {type(self.openai_client)}")
            logger.info(f"DEBUG: ShelfStructure type: {type(ShelfStructure)}")
'''

# Find the line and insert debug
lines = content.split('\n')
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'if output_schema == "ShelfStructure":' in line and i < 850:  # Make sure it's the right one
        new_lines.append(debug_line)

# Write back
with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/extraction/engine.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Added debug logging to extraction engine")