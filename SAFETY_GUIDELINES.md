# Safety Guidelines for Database Operations

## Never Do This
```python
# ❌ NEVER hardcode production IDs
supabase.table("queue").update(data).eq("id", 9).execute()

# ❌ NEVER update without backing up
result = supabase.table("queue").update({"data": new_data})
```

## Always Do This
```python
# ✅ Use environment checks
if os.getenv('ENVIRONMENT') == 'production':
    raise Exception("Cannot run in production!")

# ✅ Create backups before updates
backup = create_backup(table, id)
result = safe_update(table, id, data)

# ✅ Use transactions and rollback capability
with database.transaction() as txn:
    txn.update(...)
    if not verify_update():
        txn.rollback()
```

## Best Practices
1. Separate dev/staging/prod environments
2. Use read-only credentials for analysis
3. Require approval for production changes
4. Always backup before modifications
5. Use feature flags for testing
6. Mark test data clearly
