#!/usr/bin/env python3
"""
Test script to verify the Results page sidebar functionality
"""
import os
import webbrowser
from pathlib import Path

def test_results_sidebar():
    """Open the dashboard to test the Results page sidebar"""
    
    # Get the path to the dashboard
    dashboard_path = Path(__file__).parent / "new_dashboard.html"
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard file not found at {dashboard_path}")
        return
    
    # Create file URL
    file_url = f"file://{dashboard_path.absolute()}"
    
    print(f"Opening dashboard at: {file_url}")
    print("\nTo test the Results page sidebar:")
    print("1. Click on the 'Results' tab in the navigation")
    print("2. Check the collapsible sidebar on the left with:")
    print("   - Filters section (Status, Store, Category, Date Range, Sort By)")
    print("   - Extractions list showing all queue items")
    print("   - Toggle button to collapse/expand the sidebar")
    print("3. Try filtering by different criteria")
    print("4. Click on different extractions to view their details")
    print("5. Check that the sidebar is responsive on smaller screens")
    
    # Open in default browser
    webbrowser.open(file_url)

if __name__ == "__main__":
    test_results_sidebar()