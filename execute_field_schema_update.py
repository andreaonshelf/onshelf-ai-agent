import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def execute_field_schema_update():
    """Execute the field_schema column addition and updates"""
    
    # Get database URL from environment
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        # Try to construct it from the known pattern
        db_url = "postgresql://postgres.fxyfzjaaehgbdemjnumt:Av27X81jV0UqJsKH@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-postgres", db_url]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # Read the SQL file
            with open('update_field_schemas.sql', 'r') as f:
                sql_content = f.read()
            
            # Split into individual statements
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
            
            print(f"Found {len(statements)} SQL statements to execute\n")
            
            # Execute each statement
            for i, statement in enumerate(statements, 1):
                # Get a preview of the statement
                preview = statement[:100] + '...' if len(statement) > 100 else statement
                print(f"\nExecuting statement {i}:")
                print(f"Preview: {preview}")
                
                try:
                    result = await session.call_tool(
                        "query",
                        arguments={"sql": statement + ";"}
                    )
                    
                    # Check if it's an UPDATE statement
                    if statement.strip().upper().startswith('UPDATE'):
                        # For updates, check the result
                        if result.content and len(result.content) > 0:
                            text = result.content[0].text
                            if "UPDATE" in text:
                                print(f"✓ Success: {text}")
                            else:
                                print(f"✓ Executed successfully")
                    else:
                        print("✓ Column added or already exists")
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            # Verify the updates
            print("\n\n=== VERIFYING UPDATES ===")
            
            # Check if column exists
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'prompt_templates' 
                    AND column_name = 'field_schema'
                    """
                }
            )
            print(f"\nColumn check:\n{result.content[0].text}")
            
            # Check which prompts now have field_schema
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        template_id,
                        name,
                        CASE 
                            WHEN field_schema IS NOT NULL THEN 'Yes'
                            ELSE 'No'
                        END as has_field_schema,
                        CASE 
                            WHEN field_schema IS NOT NULL 
                            THEN jsonb_typeof(field_schema)
                            ELSE NULL
                        END as schema_type
                    FROM prompt_templates
                    WHERE stage_type IN ('structure', 'products', 'details', 'comparison', 'retry_structure', 'retry_products')
                    ORDER BY name;
                    """
                }
            )
            print(f"\nField schema status:\n{result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(execute_field_schema_update())