# 🚀 OnShelf AI Critical Fixes Installation Guide

This guide walks you through implementing all critical fixes to transform the OnShelf AI system from mock implementations to production-ready code.

## 📋 Prerequisites

- Python 3.8+
- Access to OpenAI, Anthropic, and Google AI APIs
- Supabase account and project
- Git repository access

## 🔧 Step 1: Install Dependencies

```bash
# Install critical fixes dependencies
pip install -r requirements_critical_fixes.txt

# Core dependencies
pip install google-generativeai>=0.3.0
pip install supabase>=2.0.0
pip install Pillow>=9.0.0
```

## 🗄️ Step 2: Database Setup

### Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and service key

### Run Database Schema
```sql
-- Copy and run the contents of database_schema.sql in your Supabase SQL editor
-- This creates all necessary tables for prompt management and human feedback
```

### Verify Tables Created
```sql
-- Check that these tables exist:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('human_corrections', 'prompt_templates', 'prompt_performance', 'extraction_results');
```

## 🔑 Step 3: Environment Configuration

Create or update your `.env` file:

```bash
# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_ai_api_key_here

# Supabase Database (Required for persistence)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Optional Configuration
TARGET_ACCURACY=0.95
MAX_ITERATIONS=5
MAX_API_COST_PER_EXTRACTION=1.00
```

### Get API Keys

#### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys
3. Create new secret key
4. Copy and add to `.env`

#### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to API Keys
3. Create new key
4. Copy and add to `.env`

#### Google AI API Key
1. Go to [makersuite.google.com](https://makersuite.google.com)
2. Get API key
3. Copy and add to `.env`

## 🧪 Step 4: Run Critical Fixes Tests

```bash
# Run comprehensive test suite
python test_critical_fixes.py
```

### Expected Output
```
🧪 OnShelf AI Critical Fixes Testing
==================================================

🔍 Test 1: Gemini Integration
✅ Gemini client initialized successfully

🔍 Test 2: Real API Implementations
✅ All real API implementation methods present

🔍 Test 3: Database Persistence
✅ Supabase database client initialized
✅ Database storage test completed

🔍 Test 4: Prompt Management System
✅ Model-specific prompt adjustments working
   Claude prompt length: 892
   GPT-4o prompt length: 945
   Gemini prompt length: 923

🔍 Test 5: 3-Model Consensus Voting
✅ 3-model weighted consensus voting working
   Consensus strength: 0.85
   Participating models: ['claude', 'gpt4o', 'gemini']

🔍 Test 6: Cost Tracking Accuracy
✅ Real cost tracking implemented
   GPT-4o cost (1000 tokens): $0.0220
   Claude cost (700+300 tokens): $0.0128
   Gemini cost (1000 tokens): $0.0004

==================================================
🎯 CRITICAL FIXES TEST REPORT
==================================================
Total Tests: 6
Passed: 6 ✅
Failed: 0 ❌
Success Rate: 100.0%

🎉 All critical fixes implemented successfully!
   System is ready for production deployment.
```

## 🚀 Step 5: Start the System

```bash
# Start the main application
python main.py
```

### Verify System is Running
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "2.0.0",
  "architecture": "strategic_multi_system",
  "features": [
    "gemini_integration",
    "database_persistence", 
    "prompt_management",
    "consensus_voting"
  ]
}
```

## 🎯 Step 6: Test Strategic Systems

### Test Single System Extraction
```bash
curl -X POST "http://localhost:8000/api/strategic/extract-single" \
  -F "file=@test_image.jpg" \
  -F "system_type=custom"
```

### Test Strategic Comparison
```bash
curl -X POST "http://localhost:8000/api/strategic/extract-comparison" \
  -F "file=@test_image.jpg" \
  -F "systems=custom,langgraph,hybrid"
```

### Test Prompt Analytics
```bash
curl "http://localhost:8000/api/strategic/prompt-analytics?days=30"
```

## 🔍 Step 7: Verify All Fixes

### ✅ Fix 1: Gemini Integration
- [ ] Gemini client initializes without errors
- [ ] Can process images with Gemini model
- [ ] Cost tracking works for Gemini API calls

### ✅ Fix 2: Real API Implementations
- [ ] No more mock data in structure analysis
- [ ] All 3 models (GPT-4o, Claude, Gemini) return real results
- [ ] Proper error handling for API failures

### ✅ Fix 3: Database Persistence
- [ ] Human corrections stored in Supabase
- [ ] Prompt templates persisted to database
- [ ] Performance metrics tracked over time

### ✅ Fix 4: Prompt Management System
- [ ] Model-specific prompts generated
- [ ] Database functions for prompt selection work
- [ ] Performance-based prompt optimization

### ✅ Fix 5: 3-Model Consensus Voting
- [ ] Weighted voting with all 3 models
- [ ] Confidence-based consensus decisions
- [ ] Proper handling of model disagreements

### ✅ Fix 6: Cost Tracking Accuracy
- [ ] Real API costs calculated correctly
- [ ] Token usage tracked accurately
- [ ] Cost per accuracy metrics available

## 🐛 Troubleshooting

### Common Issues

#### Gemini Import Error
```bash
# Install Google GenerativeAI
pip install google-generativeai

# Verify installation
python -c "import google.generativeai; print('Gemini OK')"
```

#### Supabase Connection Error
```bash
# Install Supabase client
pip install supabase

# Test connection
python -c "
from supabase import create_client
client = create_client('YOUR_URL', 'YOUR_KEY')
print('Supabase OK')
"
```

#### API Key Issues
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY  
echo $GOOGLE_API_KEY
echo $SUPABASE_URL
```

#### Database Schema Issues
```sql
-- Check if tables exist
\dt

-- If missing, re-run database_schema.sql
```

### Performance Issues

#### Slow API Responses
- Check API rate limits
- Verify network connectivity
- Consider implementing request caching

#### High Costs
- Review cost tracking settings
- Adjust MAX_API_COST_PER_EXTRACTION
- Monitor token usage patterns

## 📊 Monitoring and Analytics

### View Prompt Performance
```bash
curl "http://localhost:8000/api/strategic/prompt-analytics"
```

### Check Learning Statistics
```bash
curl "http://localhost:8000/api/strategic/learning-statistics?days=7"
```

### Database Analytics
```sql
-- View prompt performance
SELECT * FROM prompt_analytics;

-- View correction trends  
SELECT * FROM correction_trends;

-- Check recent extractions
SELECT system_type, AVG(overall_accuracy), COUNT(*) 
FROM extraction_results 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY system_type;
```

## 🎯 Next Steps

1. **Production Deployment**
   - Set up proper environment variables
   - Configure load balancing
   - Set up monitoring and alerting

2. **Performance Optimization**
   - Monitor API costs and usage
   - Optimize prompt templates based on feedback
   - Fine-tune consensus voting thresholds

3. **Human Feedback Integration**
   - Set up human review workflows
   - Train team on feedback submission
   - Monitor learning system improvements

4. **Scaling Considerations**
   - Implement request queuing
   - Add caching layers
   - Consider model fine-tuning

## 📞 Support

If you encounter issues:

1. Check the test report: `critical_fixes_test_report.json`
2. Review application logs
3. Verify all environment variables are set
4. Ensure database schema is properly installed
5. Test individual components using the test script

---

**🎉 Congratulations! Your OnShelf AI system is now production-ready with all critical fixes implemented.** 