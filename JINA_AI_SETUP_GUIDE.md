# Jina AI Configuration Guide

## Step 1: Get Jina AI API Key

1. Visit: https://jina.ai/
2. Sign up for a free account
3. Navigate to the API Keys section in your dashboard
4. Generate a new API key
5. Copy the API key (it will look like: jina_xxxxxxxxxxxxxxxxxxxx)

## Step 2: Configure Environment Variables

Add the following to your `.env` file:

```bash
# Jina AI Configuration
JINA_API_KEY=your_actual_jina_api_key_here
JINA_READER_ENDPOINT=https://r.jina.ai
JINA_SEARCH_ENDPOINT=https://s.jina.ai
JINA_EMBEDDINGS_ENDPOINT=https://api.jina.ai/v1/embeddings
JINA_RERANKER_ENDPOINT=https://api.jina.ai/v1/rerank
```

## Step 3: Test Configuration

Run the configuration test:
```bash
python test_jina_ai_config_simple.py
```

## Step 4: Verify Integration

Once configured, the Smart Scraper AI will use Jina AI for:
- PDF document processing (via Reader API)
- Web content analysis (via Reader API)
- Text embeddings (via Embeddings API)
- Document reranking (via Reranker API)
- Web search capabilities (via Search API)

## API Usage Limits

- Free tier: 1,000 requests per month
- Paid tiers available for higher usage
- Check current limits at: https://jina.ai/pricing

## Troubleshooting

### Common Issues:
1. **401 Authentication Error**: Invalid or missing API key
2. **Rate Limiting**: Exceeded free tier limits
3. **Network Issues**: Check internet connectivity

### Solutions:
1. Verify API key is correctly set in environment
2. Check API usage in Jina AI dashboard
3. Ensure proper network connectivity

## Integration Status

The Smart Scraper AI is now configured to use:
- ✅ crawl4ai Docker service (Primary Scraping Engine)
- ✅ Jina AI APIs (Core AI Processing Engine)

This provides the complete intelligent web scraping stack as originally designed.
