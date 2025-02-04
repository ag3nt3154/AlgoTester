from utils.data_fetcher import DataFetcher


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Algotron Data Fetcher")
    parser.add_argument("--update", action="store_true", help="Update existing data")
    parser.add_argument("--new-tickers", nargs="+", help="List of new tickers to fetch")
    parser.add_argument("--new-macro", nargs="+", help="List of new FRED series to fetch")
    
    args = parser.parse_args()
    fetcher = DataFetcher()
    
    if args.update:
        fetcher.update_existing_data()
    if args.new_tickers:
        fetcher.load_new_data(tickers=args.new_tickers)
    if args.new_macro:
        fetcher.load_new_data(macro_series=args.new_macro)