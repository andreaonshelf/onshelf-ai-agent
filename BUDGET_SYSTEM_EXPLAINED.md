# Budget System Explained

## How the Budget Affects Extraction

The budget acts as a **hard cost limit** for processing each image. It controls how many iterations and API calls the system can make before stopping.

### What Happens During Extraction

1. **Cost Tracking Starts**: When extraction begins, a `CostTracker` is initialized with your budget limit
2. **Before Each API Call**: The system estimates the cost and checks if there's enough budget remaining
3. **Cost Accumulation**: Each model call adds to the running total:
   - Structure analysis
   - Product extraction
   - Detail refinement
   - Validation checks
4. **Budget Check**: If the next operation would exceed the budget, extraction stops

### What Happens When Budget Runs Out

When the budget is exceeded:
```
CostLimitExceededException: Cost limit exceeded. 
Current: £1.85, Limit: £1.50, Operation: products_extraction would add £0.35
```

The system will:
1. **Stop immediately** - No more API calls are made
2. **Save partial results** - Whatever was extracted so far is kept
3. **Mark as incomplete** - The queue item shows the budget was exhausted
4. **Log the issue** - Details about which stage exceeded the budget

### Cost Breakdown by Model (in GBP)

#### OpenAI Models
- **GPT-4o**: £0.005/1k input tokens + £0.015/1k output tokens + £0.006/image
- **GPT-4o mini**: ~60% cheaper than GPT-4o

#### Anthropic Models  
- **Claude 4 Opus**: £0.015/1k input tokens + £0.075/1k output tokens + £0.004/image
- **Claude 4 Sonnet**: £0.003/1k input tokens + £0.015/1k output tokens + £0.004/image

#### Google Models
- **Gemini 2.5 Pro**: £0.00125/1k input chars + £0.005/1k output chars
- **Gemini 2.5 Flash**: ~80% cheaper than Pro

### Typical Cost Per Iteration

| Complexity | Structure | Products | Validation | Total per Iteration |
|------------|-----------|----------|------------|-------------------|
| Simple shelf (10-20 products) | £0.10-0.15 | £0.20-0.30 | £0.05-0.10 | £0.35-0.55 |
| Medium shelf (30-50 products) | £0.15-0.20 | £0.35-0.50 | £0.10-0.15 | £0.60-0.85 |
| Complex display (100+ products) | £0.20-0.30 | £0.60-0.90 | £0.15-0.25 | £0.95-1.45 |

### Recommended Budget Settings

#### £2.00 (Default Recommendation)
- **Why**: Allows 2-4 complete iterations for most shelves
- **Good for**: Standard retail shelves, typical store displays
- **Iterations**: Usually completes in 2-3 iterations
- **Quality**: Achieves 90-95% accuracy on average

#### £1.00 (Budget Option)
- **Why**: Forces efficient single or dual iteration
- **Good for**: Simple shelves, cost-sensitive operations
- **Iterations**: Usually 1-2 iterations max
- **Quality**: 80-90% accuracy, may miss some products

#### £3.00+ (Premium Option)
- **Why**: Allows extensive refinement and validation
- **Good for**: Complex displays, high-accuracy requirements
- **Iterations**: Can do 4-6 iterations
- **Quality**: 95%+ accuracy, catches edge cases

### Budget Optimization Tips

1. **Use Cheaper Models for Simple Tasks**
   - Gemini Flash for initial structure analysis (very cheap)
   - GPT-4o mini for basic product extraction
   - Save expensive models (Opus, GPT-4) for validation

2. **Configure Stage-Specific Models**
   - Structure: 1 fast model (Gemini Flash)
   - Products: 2-3 balanced models for voting
   - Validation: 1 high-quality model (Claude Opus)

3. **Adjust Temperature**
   - Lower temperature (0.3-0.5) = More consistent, slightly cheaper
   - Higher temperature (0.7-1.0) = More creative, may need more iterations

4. **Monitor Usage Analytics**
   - Check `model_performance_analytics` view
   - See which configurations give best accuracy per £
   - Identify which stages consume most budget

### Example Budget Usage

**Scenario**: Medium complexity shelf with 40 products

```
Iteration 1: £0.75
- Structure (Gemini Flash): £0.08
- Products (GPT-4o, Claude Sonnet, Gemini Pro voting): £0.55
- Validation (Claude Opus): £0.12

Iteration 2: £0.65 (refinement)
- Products refinement (GPT-4o): £0.35
- Validation (Claude Opus): £0.30

Total: £1.40 (within £2.00 budget)
Result: 94% accuracy
```

### When to Increase Budget

Consider increasing budget when:
- Processing high-value inventory (accuracy critical)
- Complex multi-shelf displays
- Poor lighting or image quality requires more iterations
- Need 95%+ accuracy consistently

### When to Decrease Budget

Consider decreasing budget when:
- Processing simple, well-organized shelves
- High volume, cost-sensitive operations
- Testing or development work
- Accuracy of 85-90% is acceptable

## Integration with Your System

The budget you set in the UI is passed through the entire pipeline:
1. **UI Configuration**: Set in the Extraction Config page
2. **Queue Processing**: Included in the process request
3. **Orchestrator**: Enforced by CostTracker
4. **Analytics**: Tracked in model_usage table

This ensures you never spend more than intended while maximizing extraction quality within your cost constraints.