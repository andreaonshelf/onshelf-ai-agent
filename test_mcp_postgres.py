#!/usr/bin/env python3

import json
import subprocess

def test_mcp_postgres():
    # The command from your MCP configuration
    cmd = [
        "docker",
        "run",
        "-i",
        "--rm",
        "mcp/postgres",
        "postgresql://andreavillani:@host.docker.internal:5432/mydb"
    ]
    
    try:
        # Run the MCP server with empty JSON input
        result = subprocess.run(cmd, input='{}', capture_output=True, text=True, timeout=30)
        
        # Parse the JSON response
        response = json.loads(result.stdout)
        
        print("MCP Server Response:")
        print(json.dumps(response, indent=2))
        
        if response["status"] == "success":
            print("\n✅ MCP Server is working correctly!")
            print(f"Connected to: {response['version']}")
        else:
            print("\n❌ MCP Server returned an error:")
            print(response["message"])
            
    except Exception as e:
        print(f"\n❌ Error running MCP server: {str(e)}")

if __name__ == "__main__":
    test_mcp_postgres() 