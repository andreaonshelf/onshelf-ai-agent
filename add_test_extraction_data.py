#!/usr/bin/env python3
"""Add test extraction data to verify results display"""

import os
import json
from supabase import create_client

# Get Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

# Test extraction data matching the expected format
test_extraction = {
    "stages": {
        "product_v1": {
            "data": [
                {
                    "name": "Coca Cola Classic",
                    "brand": "Coca-Cola",
                    "price": 2.99,
                    "shelf": 1,
                    "position": 1,
                    "facings": 3,
                    "confidence": 0.95,
                    "size": "355ml",
                    "category": "Soft Drinks"
                },
                {
                    "name": "Pepsi Regular",
                    "brand": "PepsiCo",
                    "price": 2.89,
                    "shelf": 1,
                    "position": 2,
                    "facings": 2,
                    "confidence": 0.92,
                    "size": "355ml",
                    "category": "Soft Drinks"
                },
                {
                    "name": "Sprite Lemon-Lime",
                    "brand": "Coca-Cola",
                    "price": 2.79,
                    "shelf": 2,
                    "position": 1,
                    "facings": 2,
                    "confidence": 0.88,
                    "size": "355ml",
                    "category": "Soft Drinks"
                },
                {
                    "name": "Mountain Dew",
                    "brand": "PepsiCo",
                    "price": 2.99,
                    "shelf": 2,
                    "position": 2,
                    "facings": 1,
                    "confidence": 0.90,
                    "size": "355ml",
                    "category": "Soft Drinks"
                }
            ]
        },
        "structure_v1": {
            "data": {
                "total_shelves": 3,
                "shelf_heights": [40, 40, 35],
                "total_width": 120,
                "sections": 4
            }
        }
    },
    "iterations": [
        {
            "iteration": 1,
            "accuracy": 0.85,
            "products_found": 4,
            "cost": 0.12
        }
    ],
    "total_products": 4,
    "final_accuracy": 0.91
}

# Test planogram data
test_planogram = {
    "svg": '<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg"><rect x="0" y="0" width="800" height="400" fill="#f0f0f0"/><text x="400" y="200" text-anchor="middle" font-size="24">Planogram Placeholder</text></svg>',
    "layout": {
        "shelves": 3,
        "products_positioned": 4
    }
}

# Update item 9 with test data
try:
    result = supabase.table("ai_extraction_queue").update({
        "extraction_result": test_extraction,
        "planogram_result": test_planogram,
        "final_accuracy": 0.91,
        "api_cost": 0.12,
        "iterations_completed": 1,
        "error_message": None  # Clear the error
    }).eq("id", 9).execute()
    
    if result.data:
        print("Successfully added test extraction data to item 9")
        print(f"Products in test data: {len(test_extraction['stages']['product_v1']['data'])}")
        print("\nYou can now:")
        print("1. Open the dashboard and navigate to Results")
        print("2. Click on item 9 in the sidebar")
        print("3. You should see the extracted products")
    else:
        print("Failed to update item 9")
except Exception as e:
    print(f"Error updating database: {e}")