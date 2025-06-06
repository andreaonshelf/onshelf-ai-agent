import psycopg2
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Query all fields for Product v1
query = '''
SELECT 
    id,
    category,
    version,
    field_name,
    display_name,
    field_type,
    is_required,
    parent_field,
    field_order,
    validation_rules,
    organization,
    created_at,
    updated_at
FROM field_definitions
WHERE category = 'Product' AND version = 'v1'
ORDER BY field_order, field_name;
'''

cur.execute(query)
fields = cur.fetchall()

print(f'Total fields found for Product v1: {len(fields)}')
print('\n' + '='*80 + '\n')

# Display fields in a structured way
for field in fields:
    print(f'Field: {field[3]} (ID: {field[0]})')
    print(f'  Display Name: {field[4]}')
    print(f'  Type: {field[5]}')
    print(f'  Required: {field[6]}')
    print(f'  Parent: {field[7]}')
    print(f'  Order: {field[8]}')
    print(f'  Organization: {field[10]}')
    print(f'  Created: {field[11]}')
    print(f'  Updated: {field[12]}')
    if field[9]:  # validation_rules
        print(f'  Validation: {json.dumps(field[9], indent=4)}')
    print('-' * 40)

# Now let's check for duplicates
print('\n' + '='*80 + '\n')
print('CHECKING FOR DUPLICATES:')
print('='*80 + '\n')

# Check for duplicate field names
dup_query = '''
SELECT 
    field_name,
    COUNT(*) as count,
    array_agg(id) as ids,
    array_agg(parent_field) as parents,
    array_agg(organization) as orgs
FROM field_definitions
WHERE category = 'Product' AND version = 'v1'
GROUP BY field_name
HAVING COUNT(*) > 1
ORDER BY count DESC, field_name;
'''

cur.execute(dup_query)
duplicates = cur.fetchall()

if duplicates:
    print(f'Found {len(duplicates)} fields with duplicates:\n')
    for dup in duplicates:
        print(f'Field: {dup[0]}')
        print(f'  Count: {dup[1]}')
        print(f'  IDs: {dup[2]}')
        print(f'  Parents: {dup[3]}')
        print(f'  Organizations: {dup[4]}')
        print('-' * 40)
else:
    print('No duplicate field names found.')

# Let's also check the hierarchical structure
print('\n' + '='*80 + '\n')
print('HIERARCHICAL STRUCTURE:')
print('='*80 + '\n')

# Get fields organized by parent
hier_query = '''
WITH RECURSIVE field_tree AS (
    -- Root fields
    SELECT 
        id,
        field_name,
        display_name,
        parent_field,
        field_order,
        organization,
        0 as level,
        field_name::text as path
    FROM field_definitions
    WHERE category = 'Product' 
        AND version = 'v1' 
        AND parent_field IS NULL
    
    UNION ALL
    
    -- Child fields
    SELECT 
        f.id,
        f.field_name,
        f.display_name,
        f.parent_field,
        f.field_order,
        f.organization,
        ft.level + 1,
        ft.path || ' > ' || f.field_name
    FROM field_definitions f
    INNER JOIN field_tree ft ON f.parent_field = ft.field_name
    WHERE f.category = 'Product' AND f.version = 'v1'
)
SELECT 
    level,
    field_name,
    display_name,
    parent_field,
    field_order,
    organization,
    path
FROM field_tree
ORDER BY level, field_order, field_name;
'''

cur.execute(hier_query)
hierarchy = cur.fetchall()

current_level = -1
for row in hierarchy:
    level = row[0]
    if level != current_level:
        print(f'\nLevel {level}:')
        current_level = level
    
    indent = '  ' * level
    print(f'{indent}- {row[1]} ({row[2]}) [parent: {row[3]}, order: {row[4]}, org: {row[5]}]')
    print(f'{indent}  Path: {row[6]}')

# Also let's check what the parsing might be doing wrong
print('\n' + '='*80 + '\n')
print('ANALYSIS OF STRUCTURE:')
print('='*80 + '\n')

# Check fields by organization
org_query = '''
SELECT 
    organization,
    COUNT(*) as field_count,
    array_agg(field_name ORDER BY field_order) as fields
FROM field_definitions
WHERE category = 'Product' AND version = 'v1'
GROUP BY organization
ORDER BY organization;
'''

cur.execute(org_query)
by_org = cur.fetchall()

print('Fields by organization:')
for org in by_org:
    print(f'\nOrganization: {org[0] or "NULL"}')
    print(f'  Count: {org[1]}')
    print(f'  Fields: {", ".join(org[2])}')

cur.close()
conn.close()