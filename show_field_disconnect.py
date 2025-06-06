#!/usr/bin/env python3
"""
SHOW EXACTLY WHERE THE FIELD DISCONNECT HAPPENS
"""

print("🔍 TRACING THE FIELD DISCONNECT IN CODE")
print("=" * 60)

print("\n1️⃣ YOUR FIELDS IN THE DATABASE:")
print("   Stage: structure")
print("   Field: structure_extraction (object)")
print("   Nested fields: total_shelves, shelf_sections, etc.")
print("   ✅ These are saved correctly")

print("\n2️⃣ IN custom_consensus_visual.py LINE 574:")
print("""
   if stage == 'structure':
       output_schema = 'ShelfStructure'  # <-- HARDCODED!
""")

print("\n3️⃣ IN extraction/engine.py LINE 826:")
print("""
   if output_schema == "ShelfStructure":
       response = self.openai_client.chat.completions.create(
           model=api_model,
           messages=messages,
           response_model=ShelfStructure,  # <-- USES HARDCODED CLASS!
""")

print("\n4️⃣ THE ShelfStructure CLASS (extraction/models.py):")
print("""
   class ShelfStructure(BaseModel):
       shelf_count: int              # <-- NOT YOUR FIELD!
       shelf_coordinates: List[...]  # <-- NOT YOUR FIELD!
""")

print("\n5️⃣ WHAT SHOULD BE HAPPENING:")
print("""
   # 1. Load your field definitions
   fields = stage_config['fields']  # Your structure_extraction field
   
   # 2. Build dynamic model from YOUR fields
   DynamicModel = build_model_from_fields(fields)
   
   # 3. Use YOUR model
   response = openai_client.chat.completions.create(
       response_model=DynamicModel  # <-- YOUR FIELDS!
   )
""")

print("\n6️⃣ THE FLOW:")
print("   Your Prompt → AI Model → Returns YOUR fields → Code expects DIFFERENT fields → ERROR!")

print("\n🎯 THE FIX NEEDED:")
print("   1. Stop using hardcoded 'ShelfStructure'")
print("   2. Build models from YOUR field definitions")
print("   3. Pass YOUR models to the AI")
print("   4. Expect YOUR fields back")

# Show the actual error
print("\n\n7️⃣ THAT'S WHY THE ERROR SAYS:")
print("   'shelf_coordinates Field required'")
print("   Because ShelfStructure expects shelf_coordinates")
print("   But AI returned YOUR fields (structure_extraction with total_shelves)!")