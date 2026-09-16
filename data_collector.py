#!/usr/bin/env python3
"""
Clearglassinc Aerospace Market Intelligence - Data Collector
Copyright © 2025-2030 Clearglassinc. All Rights Reserved.

Enterprise-grade data collection system using public APIs and ethical data sources.
Collects aerospace industry data for market analysis and competitive intelligence.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# ═══════════════════════════════════════════════════════════════════════════
# CLEARGLASSINC BRANDING
# ═══════════════════════════════════════════════════════════════════════════

__version__ = "5.0.0"
__copyright__ = "© 2025-2030 Clearglassinc. All Rights Reserved."
__system_name__ = "Clearglassinc Aerospace Data Collector"

# Configure logging with Clearglassinc branding
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [Clearglassinc] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# AEROSPACE COMPANY DATABASE
# ═══════════════════════════════════════════════════════════════════════════

AEROSPACE_COMPANIES = {
    "space_launch": [
        {"name": "SpaceX", "ticker": "SPACE-PRIVATE", "sector": "Commercial Space"},
        {"name": "Rocket Lab", "ticker": "RKLB", "sector": "Small Launch"},
        {"name": "Firefly Aerospace", "ticker": "FIRE-PRIVATE", "sector": "Medium Launch"},
        {"name": "Blue Origin", "ticker": "BLUE-PRIVATE", "sector": "Heavy Launch"},
        {"name": "Virgin Galactic", "ticker": "SPCE", "sector": "Space Tourism"},
        {"name": "Relativity Space", "ticker": "REL-PRIVATE", "sector": "3D Printed Rockets"},
    ],
    "defense_aerospace": [
        {"name": "Lockheed Martin", "ticker": "LMT", "sector": "Defense & Space"},
        {"name": "Boeing", "ticker": "BA", "sector": "Commercial & Defense"},
        {"name": "Northrop Grumman", "ticker": "NOC", "sector": "Defense Systems"},
        {"name": "Raytheon Technologies", "ticker": "RTX", "sector": "Defense Electronics"},
        {"name": "General Dynamics", "ticker": "GD", "sector": "Defense Platforms"},
    ],
    "satellite": [
        {"name": "Planet Labs", "ticker": "PL", "sector": "Earth Imaging"},
        {"name": "Maxar Technologies", "ticker": "MAXR", "sector": "Space Infrastructure"},
        {"name": "Spire Global", "ticker": "SPIR", "sector": "Space Data"},
        {"name": "Iridium Communications", "ticker": "IRDM", "sector": "Satellite Communications"},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
# DATA SOURCE CONNECTORS (PUBLIC APIs ONLY)
# ═══════════════════════════════════════════════════════════════════════════

class ClearglassDataCollector:
    """Main data collection engine for aerospace market intelligence."""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'Clearglassinc-Intelligence/{__version__}'
        })
        self.collected_data = {
            "metadata": {
                "system": __system_name__,
                "version": __version__,
                "copyright": __copyright__,
                "collection_timestamp": datetime.now().isoformat(),
                "data_sources": []
            },
            "companies": [],
            "market_metrics": {},
            "news_sentiment": [],
            "government_contracts": []
        }
    
    def collect_spacex_data(self) -> Dict:
        """Collect data from SpaceX public API."""
        logger.info("Collecting SpaceX launch data...")
        try:
            response = self.session.get(
                "https://api.spacexdata.com/v4/launches/latest",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            self.collected_data["metadata"]["data_sources"].append("SpaceX API")
            return {
                "company": "SpaceX",
                "latest_launch": data.get("name"),
                "success": data.get("success"),
                "date": data.get("date_utc"),
                "rocket": data.get("rocket"),
                "details": data.get("details", "N/A")
            }
        except Exception as e:
            logger.warning(f"SpaceX API error: {e}")
            return {}
    
    def collect_nasa_data(self) -> Dict:
        """Collect aerospace technology trends from NASA."""
        logger.info("Collecting NASA technology data...")
        # Demo API - replace with actual API key in production
        api_key = self.api_keys.get("nasa", "DEMO_KEY")
        
        try:
            response = self.session.get(
                f"https://api.nasa.gov/techport/api/projects",
                params={"api_key": api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                self.collected_data["metadata"]["data_sources"].append("NASA TechPort")
                return response.json()
            else:
                logger.warning(f"NASA API returned status {response.status_code}")
                return {}
        except Exception as e:
            logger.warning(f"NASA API error: {e}")
            return {}
    
    def collect_sec_filings(self, ticker: str) -> Dict:
        """
        Collect public SEC filings for aerospace companies.
        Uses SEC.gov public API (no authentication required, rate-limited).
        """
        logger.info(f"Collecting SEC filings for {ticker}...")
        
        try:
            # SEC Edgar API endpoint
            headers = {
                'User-Agent': 'Clearglassinc contact@clearglassinc.com',
                'Accept-Encoding': 'gzip, deflate'
            }
            
            # Get CIK from ticker (simplified example)
            # In production, maintain a ticker-to-CIK mapping
            response = self.session.get(
                f"https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcompany",
                    "ticker": ticker,
                    "type": "10-K",
                    "count": "10",
                    "output": "atom"
                },
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.collected_data["metadata"]["data_sources"].append(f"SEC EDGAR ({ticker})")
                return {
                    "ticker": ticker,
                    "filings_available": True,
                    "source": "SEC EDGAR",
                    "note": "Detailed parsing available in production version"
                }
            else:
                return {"ticker": ticker, "filings_available": False}
        
        except Exception as e:
            logger.warning(f"SEC API error for {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}
    
    def collect_market_sentiment(self, company_name: str) -> Dict:
        """
        Analyze market sentiment from public news sources.
        Uses NewsAPI or similar public APIs.
        """
        logger.info(f"Analyzing sentiment for {company_name}...")
        
        # Simulated sentiment analysis
        # In production, integrate with NewsAPI, Alpha Vantage, or similar
        sentiment_score = self._calculate_sentiment_score(company_name)
        
        return {
            "company": company_name,
            "sentiment_score": sentiment_score,
            "trend": "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral",
            "source": "Market Analysis Engine",
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_sentiment_score(self, company_name: str) -> float:
        """
        Calculate sentiment score using ML models.
        Placeholder for production NLP implementation.
        """
        # In production: integrate with transformers, BERT, or custom models
        import random
        return random.uniform(0.3, 0.9)  # Demo score
    
    def collect_contract_data(self) -> List[Dict]:
        """
        Collect government contract data from public sources.
        Uses USASpending.gov API or similar public databases.
        """
        logger.info("Collecting government contract data...")
        
        try:
            # USASpending.gov API endpoint (public, no key required)
            response = self.session.post(
                "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                json={
                    "filters": {
                        "keywords": ["aerospace", "space", "satellite", "rocket"],
                        "time_period": [
                            {"start_date": "2023-01-01", "end_date": "2025-12-31"}
                        ]
                    },
                    "fields": ["Award ID", "Recipient Name", "Award Amount"],
                    "page": 1,
                    "limit": 100
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.collected_data["metadata"]["data_sources"].append("USASpending.gov")
                return data.get("results", [])
            else:
                logger.warning(f"USASpending API returned status {response.status_code}")
                return []
        
        except Exception as e:
            logger.warning(f"Contract data error: {e}")
            return []
    
    def collect_industry_metrics(self, sector: str) -> Dict:
        """Collect industry-wide performance metrics."""
        logger.info(f"Collecting metrics for sector: {sector}")
        
        companies = AEROSPACE_COMPANIES.get(sector, [])
        metrics = {
            "sector": sector,
            "company_count": len(companies),
            "companies": [],
            "market_overview": {
                "total_revenue_estimate": "$XXB",  # Would fetch from financial APIs
                "yoy_growth": "XX%",
                "top_trends": [
                    "Increased commercial space activity",
                    "Government defense spending",
                    "Satellite constellation expansion"
                ]
            }
        }
        
        for company in companies:
            company_data = {
                "name": company["name"],
                "ticker": company["ticker"],
                "sector": company["sector"],
                "data_collected": datetime.now().isoformat()
            }
            
            # Collect SEC data for public companies
            if "-PRIVATE" not in company["ticker"]:
                sec_data = self.collect_sec_filings(company["ticker"])
                company_data["sec_filings"] = sec_data
                time.sleep(0.5)  # Respect SEC rate limits (10 requests/second)
            
            # Collect sentiment
            sentiment = self.collect_market_sentiment(company["name"])
            company_data["sentiment"] = sentiment
            
            metrics["companies"].append(company_data)
        
        return metrics
    
    def run_full_collection(self, sector_filter: str = "all") -> Dict:
        """Execute comprehensive data collection pipeline."""
        logger.info("=" * 70)
        logger.info(f"Starting Clearglassinc data collection")
        logger.info(f"Version: {__version__}")
        logger.info(f"Sector filter: {sector_filter}")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
        # Collect SpaceX data (public API)
        spacex_data = self.collect_spacex_data()
        if spacex_data:
            self.collected_data["companies"].append(spacex_data)
        
        # Collect NASA technology trends
        nasa_data = self.collect_nasa_data()
        if nasa_data:
            self.collected_data["market_metrics"]["nasa_technology"] = nasa_data
        
        # Collect contract data
        contracts = self.collect_contract_data()
        self.collected_data["government_contracts"] = contracts
        
        # Collect sector-specific data
        if sector_filter == "all" or sector_filter == "aerospace_defense":
            for sector in AEROSPACE_COMPANIES.keys():
                logger.info(f"\nProcessing sector: {sector}")
                sector_metrics = self.collect_industry_metrics(sector)
                self.collected_data["market_metrics"][sector] = sector_metrics
        else:
            # Single sector
            if sector_filter in AEROSPACE_COMPANIES:
                sector_metrics = self.collect_industry_metrics(sector_filter)
                self.collected_data["market_metrics"][sector_filter] = sector_metrics
        
        # Add collection summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.collected_data["metadata"]["collection_duration_seconds"] = duration
        self.collected_data["metadata"]["collection_completed"] = end_time.isoformat()
        self.collected_data["metadata"]["total_companies"] = len(self.collected_data["companies"])
        
        logger.info("=" * 70)
        logger.info(f"Collection completed in {duration:.2f} seconds")
        logger.info(f"Total companies: {len(self.collected_data['companies'])}")
        logger.info(f"Data sources: {len(self.collected_data['metadata']['data_sources'])}")
        logger.info("=" * 70)
        
        return self.collected_data

# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=f"{__system_name__} v{__version__}",
        epilog=__copyright__
    )
    parser.add_argument("--sector", default="aerospace_defense",
                        help="Target sector: space_launch, defense_aerospace, satellite, or all")
    parser.add_argument("--output", required=True,
                        help="Output JSON file path")
    parser.add_argument("--realtime", action="store_true",
                        help="Enable real-time monitoring mode")
    parser.add_argument("--api-keys", type=str,
                        help="JSON file with API keys (optional)")
    
    args = parser.parse_args()
    
    # Load API keys if provided
    api_keys = {}
    if args.api_keys:
        try:
            with open(args.api_keys, 'r') as f:
                api_keys = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load API keys: {e}")
    
    # Initialize collector
    collector = ClearglassDataCollector(api_keys=api_keys)
    
    # Run collection
    data = collector.run_full_collection(sector_filter=args.sector)
    
    # Save results
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to: {args.output}")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        sys.exit(1)
    
    logger.info(f"\n{__copyright__}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

# End of Clearglassinc Data Collector
# © 2025-2030 Clearglassinc. All Rights Reserved.
