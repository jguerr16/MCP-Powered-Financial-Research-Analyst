# NewsAPI.ai Setup Instructions

## Configuration

1. **Add your NewsAPI.ai API key to `.env`:**
   ```bash
   NEWS_API_KEY=your_actual_newsapi_ai_key_here
   ```

2. **If newsapi.ai uses a different endpoint, set it:**
   ```bash
   NEWS_API_ENDPOINT=https://newsapi.ai/api/v2/everything
   ```
   
   Note: The default endpoint is `https://newsapi.org/v2/everything`. If newsapi.ai uses a different format, update this.

## Testing

After updating your `.env` file, test the integration:

```bash
source .venv/bin/activate
PYTHONPATH=src python3.13 -c "
from mcp_analyst.tools.news import fetch_news
news = fetch_news('UBER', 'Uber Technologies')
print(f'Fetched {len(news)} articles')
"
```

## Material Events Feature

Once configured, the material events feature will:
- Fetch recent news articles (30-90 days)
- Analyze sentiment using VADER
- Score materiality based on recency, category, and keywords
- Display top 5 material events in the ValSum sheet with sentiment colors

## Troubleshooting

- **401 Unauthorized**: Check that your API key is correct
- **No articles returned**: Verify the endpoint URL matches newsapi.ai's documentation
- **JSON decode errors**: The endpoint might be returning HTML instead of JSON - check the endpoint URL

