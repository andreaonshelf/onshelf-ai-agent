# Environment Setup Guide

## Quick Start

1. Copy the appropriate template for your environment:
   ```bash
   cp .env.development.template .env
   ```

2. Fill in the actual values in `.env`

3. Set your environment:
   ```bash
   export ENVIRONMENT=development  # or staging, production, test
   ```

## Environment Types

### Development
- Full access to all operations
- Detailed logging
- Test data allowed
- Confirmations required for dangerous operations

### Staging  
- Limited dangerous operations
- Production-like settings
- No test data allowed
- Full monitoring enabled

### Production
- No dangerous operations allowed
- Minimal logging (warnings and errors only)
- No test data allowed
- Full monitoring and alerting
- Read-only database access for most operations
- API authentication required

### Test
- Used for automated testing
- Fast timeouts
- No confirmations
- Mock API calls available

## Security Best Practices

1. **Never commit .env files** - They're in .gitignore
2. **Use different API keys** for each environment
3. **Restrict production database access** - Use read-only credentials where possible
4. **Enable monitoring** in production
5. **Set up alerts** for production failures

## Database Separation

Each environment should have its own database:
- `development_db` - Local development
- `staging_db` - Staging tests
- `production_db` - Live data (restricted access)
- `test_db` - Automated tests (cleaned after each run)

## Verification

Check your current environment:
```python
from src.config import get_config
config = get_config()
print(f"Environment: {config.environment}")
print(f"Is Production: {config.is_production}")
print(f"Allows Dangerous Ops: {config.allows_dangerous_operations}")
```

## Migration Checklist

- [ ] Create separate databases for each environment
- [ ] Set up environment-specific API keys
- [ ] Configure monitoring for production
- [ ] Set up backup procedures
- [ ] Test dangerous operation blocks
- [ ] Verify test data rejection in production
- [ ] Set up alerting webhooks
- [ ] Document emergency procedures
