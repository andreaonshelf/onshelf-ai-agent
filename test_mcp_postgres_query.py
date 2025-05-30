#!/usr/bin/env python3

import json
import subprocess
import sys

def execute_query(query):
    # The command from your MCP configuration
    cmd = [
        "docker",
        "run",
        "-i",
        "--rm",
        "mcp/postgres",
        "postgresql://andreavillani@host.docker.internal:5432/mydb"
    ]
    
    try:
        # Run the MCP server with the query
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send the query
        stdout, stderr = process.communicate(input=json.dumps({"query": query}))
        
        if stderr:
            print(f"Error: {stderr}")
            return
            
        # Parse the response
        response = json.loads(stdout)
        print("\nQuery Result:")
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Example query to create a test table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS test_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Example query to insert data
    insert_query = """
    INSERT INTO test_table (name) VALUES ('Test Entry');
    """
    
    # Example query to select data
    select_query = """
    SELECT * FROM test_table;
    """
    
    print("Creating test table...")
    execute_query(create_table_query)
    
    print("\nInserting test data...")
    execute_query(insert_query)
    
    print("\nSelecting data...")
    execute_query(select_query) 