"""
Test Data Fixtures
Safe test data generation that doesn't touch production
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

class TestDataFactory:
    """Generate test data without touching production database"""
    
    @staticmethod
    def create_test_extraction(
        store_name: str = "Test Store",
        products_count: int = 4,
        mark_as_test: bool = True
    ) -> Dict[str, Any]:
        """Create a test extraction result"""
        
        # Generate test products
        test_products = []
        test_brands = ["TestBrand", "MockCo", "DummyInc", "ExampleCorp"]
        test_product_names = ["TestProduct", "MockItem", "DummyGoods", "ExampleWare"]
        
        for i in range(products_count):
            product = {
                "name": f"{random.choice(test_product_names)} {i+1}",
                "brand": random.choice(test_brands),
                "price": round(random.uniform(1.99, 9.99), 2),
                "shelf": random.randint(1, 3),
                "position": i + 1,
                "facings": random.randint(1, 3),
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "size": f"{random.randint(100, 500)}ml",
                "category": "Test Category"
            }
            test_products.append(product)
        
        extraction_result = {
            "stages": {
                "product_v1": {
                    "data": test_products
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
                    "accuracy": round(random.uniform(0.80, 0.95), 2),
                    "products_found": products_count,
                    "cost": round(random.uniform(0.05, 0.20), 3)
                }
            ],
            "total_products": products_count,
            "final_accuracy": round(random.uniform(0.85, 0.95), 2)
        }
        
        # Mark as test data
        if mark_as_test:
            extraction_result["is_test_data"] = True
            extraction_result["test_data_warning"] = "This is test data - not from real extraction"
        
        return {
            "id": f"test_{uuid.uuid4()}",
            "store_name": store_name,
            "status": "completed",
            "extraction_result": extraction_result,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "api_cost": round(random.uniform(0.05, 0.20), 3),
            "is_test_data": True
        }
    
    @staticmethod
    def create_test_queue_item(
        status: str = "pending",
        with_extraction: bool = False
    ) -> Dict[str, Any]:
        """Create a test queue item"""
        item = {
            "id": f"test_queue_{uuid.uuid4()}",
            "upload_id": f"test_upload_{uuid.uuid4()}",
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
            "is_test_data": True
        }
        
        if with_extraction and status == "completed":
            extraction = TestDataFactory.create_test_extraction()
            item["extraction_result"] = extraction["extraction_result"]
            item["completed_at"] = extraction["completed_at"]
            item["api_cost"] = extraction["api_cost"]
        
        return item
    
    @staticmethod
    def create_test_planogram() -> Dict[str, Any]:
        """Create a test planogram"""
        return {
            "svg": '''<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
                <rect x="0" y="0" width="800" height="400" fill="#f0f0f0"/>
                <text x="400" y="200" text-anchor="middle" font-size="24" fill="#666">
                    TEST PLANOGRAM - Not Real Data
                </text>
                <text x="400" y="230" text-anchor="middle" font-size="16" fill="#999">
                    This is test data for development only
                </text>
            </svg>''',
            "layout": {
                "shelves": 3,
                "products_positioned": 4,
                "is_test": True
            }
        }
    
    @staticmethod
    def create_realistic_test_products(category: str = "beverages") -> List[Dict[str, Any]]:
        """Create realistic-looking test products for specific categories"""
        
        # Test product templates by category
        templates = {
            "beverages": [
                {"brand": "TestBev", "name": "Sparkling Water Test", "size": "500ml"},
                {"brand": "MockDrink", "name": "Energy Drink Test", "size": "250ml"},
                {"brand": "DummyCola", "name": "Cola Zero Test", "size": "330ml"},
            ],
            "snacks": [
                {"brand": "TestSnax", "name": "Potato Chips Test", "size": "150g"},
                {"brand": "MockMunch", "name": "Chocolate Bar Test", "size": "50g"},
                {"brand": "DummyTreats", "name": "Cookies Test", "size": "200g"},
            ],
            "dairy": [
                {"brand": "TestDairy", "name": "Milk 2% Test", "size": "1L"},
                {"brand": "MockFarm", "name": "Yogurt Test", "size": "150g"},
                {"brand": "DummyCheese", "name": "Cheddar Test", "size": "200g"},
            ]
        }
        
        products = []
        product_templates = templates.get(category, templates["beverages"])
        
        for i, template in enumerate(product_templates):
            product = {
                **template,
                "price": round(random.uniform(0.99, 4.99), 2),
                "shelf": (i // 3) + 1,
                "position": (i % 3) + 1,
                "facings": random.randint(1, 3),
                "confidence": round(random.uniform(0.85, 0.95), 2),
                "category": category,
                "is_test_data": True
            }
            products.append(product)
        
        return products


class TestDataContext:
    """Context manager for test data lifecycle"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.created_records = []
        
    def __enter__(self):
        """Set up test data context"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up test data"""
        if self.supabase:
            # Clean up any test data created during the context
            for record in self.created_records:
                try:
                    self.supabase.table(record['table']).delete().eq(
                        'id', record['id']
                    ).execute()
                except:
                    pass
        self.created_records.clear()
    
    def create_test_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test record that will be cleaned up"""
        # Ensure it's marked as test data
        data['is_test_data'] = True
        data['test_context_id'] = str(uuid.uuid4())
        
        if self.supabase:
            result = self.supabase.table(table).insert(data).execute()
            if result.data:
                self.created_records.append({
                    'table': table,
                    'id': result.data[0]['id']
                })
                return result.data[0]
        
        return data


# Example usage for testing UI without touching production
def get_test_results_for_ui():
    """Get test results for UI development"""
    return {
        "queue_items": [
            TestDataFactory.create_test_queue_item("completed", with_extraction=True),
            TestDataFactory.create_test_queue_item("processing"),
            TestDataFactory.create_test_queue_item("pending"),
        ],
        "message": "Using test data - not connected to production"
    }


# Example usage for integration testing
def test_extraction_flow_with_fixtures():
    """Test extraction flow without real data"""
    
    # Create test extraction
    test_extraction = TestDataFactory.create_test_extraction(
        store_name="Test Co-op Store",
        products_count=6
    )
    
    # Simulate processing
    print(f"Processing test extraction: {test_extraction['id']}")
    print(f"Found {test_extraction['extraction_result']['total_products']} products")
    print(f"Cost: ${test_extraction['api_cost']}")
    
    # Validate results
    assert test_extraction['is_test_data'] == True
    assert test_extraction['extraction_result']['total_products'] == 6
    
    return test_extraction