import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL and key
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

print(f"Supabase URL: {supabase_url}")
print(f"Key present: {'Yes' if supabase_key else 'No'}")

# The database URL pattern for Supabase
if supabase_url:
    # Extract project ID from URL
    project_id = supabase_url.split('//')[1].split('.')[0]
    
    # Construct database URL
    # Default Supabase pattern: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
    db_url = f"postgresql://postgres.{project_id}:Av27X81jV0UqJsKH@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print(f"\nConstructed DB URL (template):")
    print(db_url)
    print("\nNote: You'll need the actual database password from your Supabase dashboard")
    print("Go to: Settings > Database > Connection string")