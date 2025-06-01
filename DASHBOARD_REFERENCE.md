# Dashboard Reference

## IMPORTANT: Which Dashboard to Use

### Current Active Dashboard: `/react`
- **URL**: http://localhost:8000/react
- **File**: `new_dashboard_6am.html` (extracted from commit ed52664 at 6:04 AM on May 31, 2025)
- **Description**: This is the working React dashboard with the unified interface
- **Status**: ACTIVE - Use this for all development

### Deprecated Dashboard: `/` (root)
- **URL**: http://localhost:8000/
- **File**: Inline HTML in `main.py`
- **Description**: Old dashboard from days ago, no longer in active development
- **Status**: DEPRECATED - Do not use

## Development Notes

When working on the dashboard:
1. Always use http://localhost:8000/react
2. The dashboard file is `new_dashboard_6am.html`
3. This dashboard includes:
   - Queue Management
   - Model Configuration
   - Stage Configuration
   - Analytics
   - Field Definitions

## Next Steps
Implement the features from CHANGES_SINCE_LAST_COMMIT.md in the React dashboard at `/react`.