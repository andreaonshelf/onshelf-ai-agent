#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("Error: DATABASE_URL not found in environment variables")
    exit(1)

# Read SQL file
with open('add_field_definition_organization.sql', 'r') as f:
    sql_content = f.read()

# Connect and execute
try:
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    print("Running field definition organization migration...")
    cur.execute(sql_content)
    conn.commit()
    
    print("Migration completed successfully!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error running migration: {e}")
    exit(1)