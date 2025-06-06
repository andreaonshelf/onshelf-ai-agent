-- Remove fake 91% accuracy from item #9
UPDATE ai_extraction_queue 
SET final_accuracy = NULL 
WHERE id = 9;

-- Also remove any other suspiciously round accuracy values
UPDATE ai_extraction_queue 
SET final_accuracy = NULL 
WHERE final_accuracy IN (0.91, 0.80, 0.85, 0.90, 0.95, 0.75, 0.70)
AND (extraction_result IS NULL OR extraction_result = '{}');