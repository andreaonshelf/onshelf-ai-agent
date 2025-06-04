import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def investigate_prompts():
    """Investigate prompt_templates table structure and duplicates"""
    
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
            
            # 1. Check current table structure
            print("1. Checking prompt_templates structure:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = 'prompt_templates'
                    ORDER BY ordinal_position;
                    """
                }
            )
            print(f"Table Structure:\n{result.content[0].text}\n")
            
            # 2. Check for duplicates
            print("2. Checking for duplicate names:")
            result = await session.call_tool(
                "query", 
                arguments={
                    "sql": """
                    SELECT 
                        name, 
                        stage_type,
                        COUNT(*) as count,
                        string_agg(template_id::text, ', ' ORDER BY created_at) as template_ids
                    FROM prompt_templates
                    WHERE name IS NOT NULL
                    GROUP BY name, stage_type
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC, name;
                    """
                }
            )
            print(f"Duplicates Found:\n{result.content[0].text}\n")
            
            # 3. Look at the specific problematic prompt
            print("3. Examining 'custom_structure_gpt4o_v2.0' prompts:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        prompt_id,
                        template_id,
                        name,
                        prompt_type,
                        stage_type,
                        model_type,
                        created_at
                    FROM prompt_templates
                    WHERE name = 'custom_structure_gpt4o_v2.0'
                    OR template_id = 'custom_structure_gpt4o_v2.0'
                    ORDER BY created_at;
                    """
                }
            )
            print(f"Specific Prompt Details:\n{result.content[0].text}\n")
            
            # 4. Check if name column already exists
            print("4. Checking if migration was partially applied:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        COUNT(*) as prompts_with_names,
                        COUNT(DISTINCT name) as unique_names,
                        COUNT(*) FILTER (WHERE name IS NULL) as prompts_without_names
                    FROM prompt_templates;
                    """
                }
            )
            print(f"Name Column Status:\n{result.content[0].text}\n")
            
            # 5. Check existing constraints
            print("5. Checking existing constraints:")
            result = await session.call_tool(
                "query",
                arguments={
                    "sql": """
                    SELECT 
                        conname as constraint_name,
                        contype as constraint_type,
                        pg_get_constraintdef(oid) as definition
                    FROM pg_constraint
                    WHERE conrelid = 'prompt_templates'::regclass
                    ORDER BY conname;
                    """
                }
            )
            print(f"Existing Constraints:\n{result.content[0].text}\n")

if __name__ == "__main__":
    asyncio.run(investigate_prompts())