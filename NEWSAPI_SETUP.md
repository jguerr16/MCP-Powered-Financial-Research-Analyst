# Event Registry (NewsAPI.ai) Setup Instructions

**Version 3.0** - This project uses Event Registry (newsapi.ai) for news and sentiment analysis.

## Configuration

1. **Get your Event Registry API key:**
   - Sign up at [newsapi.ai](https://newsapi.ai/dashboard)
   - Get your API key from the dashboard

2. **Add your Event Registry API key to `.env`:**
   ```bash
   NEWS_API_KEY=your_event_registry_api_key_here
   ```
   
   Note: The `NEWS_API_KEY` environment variable is used for Event Registry, not the old newsapi.org service.

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

## Material Events Feature (v3)

Once configured, the material events feature will:
- Fetch recent news articles (30-90 days) from Event Registry
- Extract sentiment scores (Event Registry provides built-in sentiment analysis)
- Fall back to VADER Sentiment if Event Registry sentiment unavailable
- Categorize events (M&A, litigation, guidance, macro)
- Score materiality based on recency, category, and keywords
- Display top 5 material events in the ValSum sheet with sentiment colors:
  - **Green**: Positive sentiment
  - **Red**: Negative sentiment
  - **Yellow**: Neutral sentiment

## Troubleshooting

- **401 Unauthorized / Invalid API Key**: 
  - Verify your API key is correct in `.env`
  - Ensure you're using an Event Registry (newsapi.ai) key, not newsapi.org
  - Check that `load_dotenv()` is being called (it should be automatic)
  
- **No articles returned**: 
  - Event Registry may not have recent articles for the ticker
  - Try a more well-known company (e.g., AAPL, MSFT, UBER)
  - Check Event Registry dashboard for API usage limits
  
- **ImportError: No module named 'eventregistry'**: 
  - Install the package: `pip install eventregistry`
  - Or reinstall dependencies: `pip install -e ".[dev]"`
  
- **Sentiment scores are 0 or missing**: 
  - Event Registry may not provide sentiment for all articles
  - The system will fall back to VADER Sentiment automatically
  - Check that `vaderSentiment` is installed: `pip install vaderSentiment`

