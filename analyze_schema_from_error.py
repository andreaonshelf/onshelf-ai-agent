"""
Analyzing the error message from pattern 4 which reveals all columns:

Failing row contains (
    465efe79-b90e-4a56-b5f3-78d1ab47234a,  # 1. UUID (probably prompt_id)
    null,                                    # 2. template_id
    null,                                    # 3. prompt_type
    null,                                    # 4. model_type  
    null,                                    # 5. prompt_version
    Test prompt,                             # 6. prompt_text (our input)
    0.000,                                   # 7. performance_score
    0,                                       # 8. usage_count
    0.000,                                   # 9. correction_rate
    f,                                       # 10. is_active
    f,                                       # 11. created_from_feedback
    null,                                    # 12. parent_prompt_id
    null,                                    # 13. retailer_context
    null,                                    # 14. category_context
    null,                                    # 15. avg_token_cost
    2025-06-05 18:25:44.749691,             # 16. created_at
    Test Minimal,                            # 17. name (our input)
    null,                                    # 18. description
    [],                                      # 19. field_definitions
    products,                                # 20. stage_type (our input)
    {},                                      # 21. tags
    null,                                    # 22. unknown
    t,                                       # 23. unknown boolean
    f,                                       # 24. unknown boolean
    0.000,                                   # 25. unknown decimal
    0,                                       # 26. unknown integer
    0.0000,                                  # 27. unknown decimal
    [],                                      # 28. fields
    f,                                       # 29. is_user_created
    0,                                       # 30. autonomy_level
    2025-06-05 18:25:44.749691+00,          # 31. updated_at
    {},                                      # 32. unknown object
    [],                                      # 33. unknown array
    {},                                      # 34. unknown object
    null,                                    # 35. unknown
    {},                                      # 36. unknown object
    null,                                    # 37. unknown
    f,                                       # 38. unknown boolean
    0,                                       # 39. version
    null                                     # 40. unknown
).
"""

# Based on this, the actual schema appears to be a mix of old and new columns
print("=== ANALYZED SCHEMA ===")
print("""
The prompt_templates table has these columns (in order):
1. prompt_id (UUID) - Primary key
2. template_id (TEXT) - NOT NULL 
3. prompt_type (TEXT)
4. model_type (TEXT)
5. prompt_version (TEXT)
6. prompt_text (TEXT) - This is where content goes
7. performance_score (DECIMAL)
8. usage_count (INTEGER)
9. correction_rate (DECIMAL)
10. is_active (BOOLEAN)
11. created_from_feedback (BOOLEAN)
12. parent_prompt_id (UUID)
13. retailer_context (TEXT[])
14. category_context (TEXT[]) 
15. avg_token_cost (DECIMAL)
16. created_at (TIMESTAMP)
17. name (VARCHAR)
18. description (TEXT)
19. field_definitions (JSONB) 
20. stage_type (VARCHAR)
21. tags (TEXT[])
22-27. Unknown columns
28. fields (JSONB)
29. is_user_created (BOOLEAN)
30. autonomy_level (INTEGER)
31. updated_at (TIMESTAMP)
32-38. Unknown columns
39. version (INTEGER)
40. Unknown column

Key findings:
- template_id is NOT NULL (required)
- The content column is called 'prompt_text' not 'prompt_content' or 'content'
- Both 'field_definitions' and 'fields' columns exist
- Both old schema (template_id, prompt_type, model_type) and new schema (name, stage_type) columns exist
""")