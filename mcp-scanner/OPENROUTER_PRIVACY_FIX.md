# OpenRouter Privacy Configuration Issue

## Problem

Your OpenRouter API key has strict data privacy settings that are blocking free models.

## Error Message

```
Error code: 404 - No endpoints found matching your data policy (Free model publication).
Configure: https://openrouter.ai/settings/privacy
```

## Solution

Go to: **<https://openrouter.ai/settings/privacy>**

You need to allow your data to be used for model training to access free models.

### Options

1. **Allow free models**: Change privacy settings to allow free model access
2. **Use paid models**: Keep current privacy settings but use paid models instead (requires credits)
3. **Try different free model**: Some free models might not require the same privacy policy

## Recommended Free Models (that might work)

Try these alternatives in your `.env` file:

```ini
# Option 1: Google models
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Option 2: Meta models  
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free

# Option 3: Qwen (if not rate limited)
OPENROUTER_MODEL=qwen/qwen-2-7b-instruct:free
```

## Quick Fix

1. Visit <https://openrouter.ai/settings/privacy>
2. Review and update your privacy settings
3. Try the scan again
