#!/usr/bin/env python3

import sys
import json
import psycopg2
from sqlalchemy import create_engine, text

def main():
    if len(sys.argv) < 2:
        print("Usage: python mcp_server.py <connection_string>")
        sys.exit(1)

    connection_string = sys.argv[1]
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        query = input_data.get("query")
        
        if query:
            # Execute the query
            with engine.connect() as conn:
                result = conn.execute(text(query))
                if result.returns_rows:
                    # If the query returns rows, fetch them
                    rows = [dict(row) for row in result]
                    print(json.dumps({
                        "status": "success",
                        "data": rows
                    }))
                else:
                    # If the query doesn't return rows (e.g., INSERT, UPDATE)
                    print(json.dumps({
                        "status": "success",
                        "message": "Query executed successfully"
                    }))
        else:
            # If no query provided, just test the connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.scalar()
                print(json.dumps({
                    "status": "success",
                    "message": "Connected to PostgreSQL",
                    "version": version
                }))
            
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main() 