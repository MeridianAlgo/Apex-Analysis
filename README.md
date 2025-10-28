# Apex Analysis

A comprehensive stock analysis tool that combines price data with news sentiment analysis to provide insights into stock performance.

## Features

- Real-time stock price data fetching
- News sentiment analysis
- Volatility and correlation metrics
- Combined price and sentiment visualization
- Automated report generation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/apex-analysis.git
   cd apex-analysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python main.py
```

Enter a stock ticker (e.g., AAPL) when prompted. The application will generate analysis reports in the `reports` directory.

## Project Structure

- `main.py`: Entry point of the application
- `fetch_data.py`: Handles stock data fetching using yfinance
- `news_processor.py`: Processes and fetches news articles
- `sentiment_analyzer.py`: Performs sentiment analysis on news articles
- `aggregator.py`: Aggregates and analyzes data
- `ui.py`: Command-line interface
- `utils.py`: Utility functions
- `config.py`: Configuration settings
- `reports/`: Directory for generated reports and visualizations

## Security

- Uses HTTPS for all API requests
- Respects `robots.txt` rules when scraping news
- No API keys or sensitive information is hardcoded

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

