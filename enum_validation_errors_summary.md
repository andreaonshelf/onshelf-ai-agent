# Enum Validation Errors Summary

Based on the analysis of the log files from 2025-06-07, the following enum fields are consistently failing validation:

## 1. **pricing.price_tag_location**
- **Expected values**: `'directly_below'`, `'left_of_product'`, `'right_of_product'`, `'distant'`, `'not_visible'`
- **Actual value received**: `'front'` (string)
- **Error**: The model is returning 'front' which is not in the allowed enum values

## 2. **pricing.price_attribution_confidence**
- **Expected values**: `'certain'`, `'likely'`, `'uncertain'`
- **Actual value received**: `0.95` (float)
- **Error**: The model is returning numeric confidence scores instead of enum strings

## 3. **package_info.size_read_location**
- **Expected values**: `'front_label'`, `'side_visible'`, `'cap_lid'`, `'not_visible'`
- **Actual value received**: `'front'` (string)
- **Error**: The model is returning 'front' instead of 'front_label'

## 4. **package_info.size_read_confidence**
- **Expected values**: `'certain'`, `'likely'`, `'uncertain'`
- **Actual value received**: `0.9` (float)
- **Error**: The model is returning numeric confidence scores instead of enum strings

## 5. **physical.width_relative**
- **Expected values**: `'narrow'`, `'normal'`, `'wide'`
- **Actual value received**: `0.2` (float)
- **Error**: The model is returning numeric values instead of categorical descriptions

## 6. **physical.height_relative**
- **Expected values**: `'short'`, `'medium'`, `'tall'`
- **Actual value received**: `0.3` (float)
- **Error**: The model is returning numeric values instead of categorical descriptions

## 7. **physical.dimension_confidence**
- **Expected values**: `'measured'`, `'estimated'`, `'rough_guess'`
- **Actual value received**: `0.9` (float)
- **Error**: The model is returning numeric confidence scores instead of enum strings

## 8. **quality.visibility**
- **Expected values**: `'clearly_visible'`, `'partially_obscured'`, `'mostly_hidden'`
- **Actual value received**: `'clear'` (string)
- **Error**: The model is returning 'clear' instead of 'clearly_visible'

## 9. **quality.confidence**
- **Expected values**: `'high'`, `'medium'`, `'low'`
- **Actual value received**: `0.95` (float)
- **Error**: The model is returning numeric confidence scores instead of enum strings

## Pattern Analysis

The main issues are:
1. **Numeric vs String**: Many confidence fields expect string enums but receive float values
2. **Abbreviated values**: Some fields receive shortened versions (e.g., 'front' instead of 'front_label', 'clear' instead of 'clearly_visible')
3. **Wrong data type**: Relative measurements are returning floats instead of categorical strings

## Affected Model
These errors are occurring in the `DetailsExtractionModel` during the `langgraph_details_gpt-4o` extraction process.