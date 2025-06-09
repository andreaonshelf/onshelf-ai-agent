# Quarantine Report

Date: 2025-06-09T10:21:45.173774

## Quarantined Files (18)

- HARD_RESET_ALL_DATA.py
- add_test_extraction_data.py
- test_all_systems_real_extraction.py
- test_structure_extraction.py
- test_extraction_direct.py
- cleanup_fake_data.sql
- TEST_FULL_PROCESS.py
- reset_all_queue_items.py
- delete_all_prompts.sql
- clear_all_fake_data.py
- reset_queue_item.py
- test_default_config.py
- test_config_with_fields.py
- test_prompt_database.py
- reset_failed_items.py
- reset_fake_completed.py
- test_real_extraction.py
- reset_stuck_items.py

## Reason

These scripts were quarantined because they can directly modify production data without safeguards. They should be reviewed and either:
1. Deleted if no longer needed
2. Modified to add safety checks
3. Moved to a development-only directory
