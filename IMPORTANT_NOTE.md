# IMPORTANT: Dashboard File Names

The server (main.py) serves `new_dashboard.html`, NOT `new_dashboard_working.html`.

When making changes to the dashboard:
1. Edit `new_dashboard_working.html` (the development version)
2. Copy to `new_dashboard.html` when ready to test: `cp new_dashboard_working.html new_dashboard.html`
3. Refresh browser to see changes

The insert-at-position feature has been added to `new_dashboard_working.html` and copied to `new_dashboard.html`.

## Insert Feature Details:
- Hover between fields to see "Insert field here" buttons
- Click to insert a new field at that exact position
- Works at all nesting levels
- CSS classes: `.insert-field-wrapper`, `.insert-field-button`