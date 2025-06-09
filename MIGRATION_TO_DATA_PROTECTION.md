# Scripts Requiring Data Protection Migration

Found 97 scripts with direct database access.


## QUARANTINE_dangerous_scripts/

- **TEST_FULL_PROCESS.py**: Direct update without protection
- **reset_queue_item.py**: Direct update without protection
- **test_config_with_fields.py**: Direct insert without protection
- **test_prompt_database.py**: Direct insert without protection
- **reset_failed_items.py**: Direct update without protection
- **reset_fake_completed.py**: Direct update without protection
- **test_real_extraction.py**: Direct update without protection
- **reset_stuck_items.py**: Direct update without protection

## agent/

- **agent.py**: Direct insert without protection

## api/

- **prompt_management.py**: Direct update without protection
- **queue_processing.py**: Direct update without protection
- **configurations.py**: Direct update without protection
- **extraction_config.py**: Direct update without protection
- **feedback.py**: Direct update without protection
- **planogram_editor.py**: Direct insert without protection
- **queue_management.py**: Direct update without protection
- **image_analysis.py**: Direct insert without protection
- **image_management.py**: Direct insert without protection
- **prompt_library.py**: Direct insert without protection
- **field_definitions.py**: Direct update without protection
- **analytics.py**: Direct update without protection
- **prompt_management_missing.py**: Direct update without protection

## backup_before_revert/

- **prompt_management.py**: Direct insert without protection
- **prompt_evolution.py**: Direct insert without protection
- **performance_tracker.py**: Direct insert without protection

## extract.planogram/

- **check_all_paths.py**: Direct update without protection
- **revert_model_changes.py**: Direct update without protection
- **force_process_item.py**: Direct update without protection
- **disable_gemini_temporarily.py**: Direct update without protection
- **check_media_files_detailed.py**: Direct update without protection
- **verify_prompt_table_state.py**: Direct insert without protection
- **run_field_migrations.py**: Direct PostgreSQL connection
- **fix_planogram_generation.py**: Direct update without protection
- **fix_image_paths.py**: Direct update without protection
- **backend_model_integration.py**: Direct update without protection
- **fix_all_prompt_fields.py**: Direct update without protection
- **fix_existing_queue_configs.py**: Direct update without protection
- **parse_prompts_clean.py**: Direct update without protection
- **cleanup_and_verify_prompts.py**: Direct delete operation
- **run_feedback_migration.py**: Direct PostgreSQL connection
- **fix_empty_field_configs.py**: Direct update without protection
- **check_current_schema.py**: Direct insert without protection
- **fix_queue_item_9.py**: Direct update without protection
- **find_prompt_storage.py**: Direct insert without protection
- **add_missing_prompt_endpoints.py**: Direct update without protection
- **execute_field_schema_psycopg2.py**: Direct PostgreSQL connection
- **find_image_paths.py**: Direct update without protection
- **restore_user_configs.py**: Direct update without protection
- **parse_document_to_fields.py**: Direct update without protection
- **parse_document_correctly.py**: Direct update without protection
- **add_configuration_endpoints.py**: Direct update without protection
- **check_product_fields.py**: Direct PostgreSQL connection
- **run_queue_processor.py**: Direct update without protection
- **fix_queue_item_9_final.py**: Direct update without protection
- **remove_gemini_from_queue.py**: Direct update without protection
- **check_prompt_templates_columns.py**: Direct insert without protection
- **fix_database_and_insert_prompts.py**: Direct insert without protection
- **fix_queue_item_9_properly.py**: Direct update without protection
- **fix_field_parsing_duplicates.py**: Direct update without protection
- **save_prompts_from_md.py**: Direct insert without protection
- **fix_all_queue_paths.py**: Direct update without protection
- **FORCE_REAL_EXTRACTION.py**: Direct update without protection
- **QUARANTINE_DANGEROUS_SCRIPTS.py**: Direct update without protection
- **run_extraction_runs_migration.py**: Direct PostgreSQL connection
- **run_field_definitions_migration.py**: Direct async PostgreSQL connection
- **update_field_definitions.py**: Direct update without protection
- **fix_product_v1_fields.py**: Direct update without protection
- **run_field_definitions_migration_supabase.py**: Direct insert without protection
- **fix_invalid_model_ids.py**: Direct update without protection
- **parse_extraction_prompts_complete.py**: Direct update without protection
- **execute_field_schema_supabase.py**: Direct update without protection
- **parse_and_update_prompts.py**: Direct update without protection
- **update_complete_prompts.py**: Direct update without protection
- **add_missing_prompts.py**: Direct insert without protection
- **fix_prompt_fields_format.py**: Direct update without protection
- **direct_investigate_prompts.py**: Direct PostgreSQL connection
- **execute_remaining_sqls.py**: Direct insert without protection
- **update_pydantic_schemas.py**: Direct update without protection
- **update_all_prompts_exact_fields.py**: Direct update without protection
- **update_prompts_to_v1.py**: Direct update without protection
- **build_complete_config_with_fields.py**: Direct update without protection
- **fix_all_queue_gemini.py**: Direct update without protection
- **remove_duplicates.py**: Direct update without protection
- **fix_all_invalid_model_ids.py**: Direct update without protection
- **investigate_database_state.py**: Direct PostgreSQL connection
- **fix_queue_gemini.py**: Direct update without protection
- **run_migration.py**: Direct PostgreSQL connection
- **add_model_config_column.py**: Direct PostgreSQL connection

## extraction/

- **state_tracker.py**: Direct upsert without protection
- **prompt_evolution.py**: Direct insert without protection
- **performance_tracker.py**: Direct insert without protection

## migrations/

- **final_prompt_fixes.py**: Direct insert without protection
- **check_schema_current.py**: Direct PostgreSQL connection
- **check_field_schemas.py**: Direct PostgreSQL connection

## orchestrator/

- **system_dispatcher.py**: Direct update without protection
- **master_orchestrator_backup.py**: Direct update without protection

## utils/

- **model_usage_tracker.py**: Direct update without protection

## Migration Steps

1. Add imports for DataProtection and environment config
2. Check environment before any database operations
3. Use DataProtection.safe_update() for updates
4. Add @protected_database_operation decorator to dangerous functions
5. Require confirmation for destructive operations
