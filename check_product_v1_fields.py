import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

async def check_product_v1_fields():
    """Check the exact structure of fields in Product v1 prompt"""
    
    # Get database URL from environment
    db_url = os.environ.get("SUPABASE_DB_URL", os.environ.get("DATABASE_URL"))
    if not db_url:
        print("Error: No database URL found in environment variables")
        return
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-postgres", db_url]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # 1. Get Product v1 prompt with raw fields
            print("1. Querying Product v1 prompt:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        prompt_id,
                        template_id,
                        name,
                        fields,
                        pg_typeof(fields) as fields_type,
                        length(fields::text) as fields_length
                    FROM prompt_templates
                    WHERE name LIKE '%Product%v1%'
                    OR template_id LIKE '%product%v1%'
                    LIMIT 5;
                    """
                }
            )
            print(f"Product v1 prompts found:\n{result.content[0].text}\n")
            
            # 2. Get the raw fields JSON
            print("2. Getting raw fields JSON:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        name,
                        fields::text as raw_fields
                    FROM prompt_templates
                    WHERE name LIKE '%Product%v1%'
                    OR template_id LIKE '%product%v1%'
                    LIMIT 1;
                    """
                }
            )
            print("Raw fields JSON:")
            print(result.content[0].text)
            print("\n")
            
            # 3. Check what the actual JSON structure is
            print("3. Checking JSON structure type:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        name,
                        jsonb_typeof(fields) as json_type,
                        CASE 
                            WHEN jsonb_typeof(fields) = 'array' THEN 'Array with ' || jsonb_array_length(fields) || ' elements'
                            WHEN jsonb_typeof(fields) = 'object' THEN 'Object with ' || (SELECT COUNT(*) FROM jsonb_object_keys(fields)) || ' keys'
                            ELSE 'Other type: ' || jsonb_typeof(fields)
                        END as structure_info
                    FROM prompt_templates
                    WHERE name LIKE '%Product%v1%'
                    OR template_id LIKE '%product%v1%'
                    LIMIT 5;
                    """
                }
            )
            print(f"JSON structure analysis:\n{result.content[0].text}\n")
            
            # 4. If it's an object, get the keys
            print("4. Checking object keys if applicable:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        name,
                        jsonb_object_keys(fields) as field_key
                    FROM prompt_templates
                    WHERE (name LIKE '%Product%v1%' OR template_id LIKE '%product%v1%')
                    AND jsonb_typeof(fields) = 'object'
                    LIMIT 20;
                    """
                }
            )
            print(f"Object keys:\n{result.content[0].text}\n")
            
            # 5. Get a sample of the fields data
            print("5. Getting sample fields data:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        name,
                        jsonb_pretty(fields) as pretty_fields
                    FROM prompt_templates
                    WHERE name LIKE '%Product%v1%'
                    OR template_id LIKE '%product%v1%'
                    LIMIT 1;
                    """
                }
            )
            print("Pretty printed fields:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(check_product_v1_fields())