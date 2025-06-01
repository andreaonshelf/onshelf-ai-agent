#!/usr/bin/env python3
"""Check existing database tables"""

import requests
import json

# MCP server URL
MCP_URL = "http://localhost:8765"

def execute_query(query):
    """Execute a query via MCP"""
    response = requests.post(
        f"{MCP_URL}/query",
        json={"query": query}
    )
    return response.json()

# Check all tables in public schema
print("Checking existing tables in database...")
result = execute_query("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")

print("\nExisting tables:")
print(json.dumps(result, indent=2))

# Check if prompt-related tables exist
print("\n\nChecking for prompt-related tables...")
result = execute_query("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%prompt%'
    ORDER BY table_name;
""")

print("\nPrompt-related tables:")
print(json.dumps(result, indent=2))

# Check columns of meta_prompts if it exists
print("\n\nChecking meta_prompts table structure...")
result = execute_query("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' 
    AND table_name = 'meta_prompts'
    ORDER BY ordinal_position;
""")

print("\nmeta_prompts columns:")
print(json.dumps(result, indent=2))

# Check sample data from meta_prompts
print("\n\nSample data from meta_prompts...")
result = execute_query("""
    SELECT id, stage, title
    FROM meta_prompts
    LIMIT 5;
""")

print("\nmeta_prompts sample:")
print(json.dumps(result, indent=2))