#!/usr/bin/env python3
"""
Clearglassinc Aerospace Market Intelligence - Market Analyzer
Copyright © 2025-2030 Clearglassinc. All Rights Reserved.

Advanced market analysis engine with competitive intelligence algorithms.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List
import numpy as np
from collections import defaultdict

__version__ = "5.0.0"
__copyright__ = "© 2025-2030 Clearglassinc. All Rights Reserved."

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [Clearglassinc Analyzer] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MARKET ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ClearglassMarketAnalyzer:
    """Advanced aerospace market analysis and competitive intelligence."""
    
    def __init__(self, data: Dict):
        self.raw_data = data
        self.analysis = {
            "metadata": {
                "system": "Clearglassinc Market Analyzer",
                "version": __version__,
                "copyright": __copyright__,
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "competitive_landscape": {},
            "market_share_analysis": {},
            "sentiment_analysis": {},
            "growth_indicators": {},
            "risk_assessment": {},
            "strategic_insights": []
        }
    
    def analyze_competitive_landscape(self) -> Dict:
        """Analyze competitive positioning across aerospace sectors."""
        logger.info("Analyzing competitive landscape...")
        
        landscape = {
            "sector_breakdown": {},
            "market_leaders": [],
            "emerging_players": [],
            "competitive_intensity": {}
        }
        
        # Analyze each sector
        for sector, metrics in self.raw_data.get("market_metrics", {}).items():
            if isinstance(metrics, dict) and "companies" in metrics:
                companies = metrics["companies"]
                
                sector_analysis = {
                    "company_count": len(companies),
                    "companies": [],
                    "average_sentiment": 0.0,
                    "sector_health": "healthy"
                }
                
                sentiments = []
                for company in companies:
                    sentiment_data = company.get("sentiment", {})
                    sentiment_score = sentiment_data.get("sentiment_score", 0.5)
                    sentiments.append(sentiment_score)
                    
                    company_profile = {
                        "name": company["name"],
                        "ticker": company["ticker"],
                        "sentiment_score": sentiment_score,
                        "sentiment_trend": sentiment_data.get("trend", "neutral"),
                        "market_position": self._calculate_market_position(sentiment_score)
                    }
                    sector_analysis["companies"].append(company_profile)
                
                # Calculate sector metrics
                if sentiments:
                    sector_analysis["average_sentiment"] = np.mean(sentiments)
                    sector_analysis["sentiment_std"] = np.std(sentiments)
                    sector_analysis["sector_health"] = self._assess_sector_health(
                        sector_analysis["average_sentiment"]
                    )
                
                landscape["sector_breakdown"][sector] = sector_analysis
                
                # Identify leaders and emerging players
                top_companies = sorted(
                    sector_analysis["companies"],
                    key=lambda x: x["sentiment_score"],
                    reverse=True
                )
                
                if top_companies:
                    landscape["market_leaders"].extend(top_companies[:2])
        
        self.analysis["competitive_landscape"] = landscape
        return landscape
    
    def _calculate_market_position(self, sentiment_score: float) -> str:
        """Calculate market position based on sentiment."""
        if sentiment_score >= 0.75:
            return "Market Leader"
        elif sentiment_score >= 0.60:
            return "Strong Performer"
        elif sentiment_score >= 0.45:
            return "Market Follower"
        else:
            return "Challenged Position"
    
    def _assess_sector_health(self, avg_sentiment: float) -> str:
        """Assess overall sector health."""
        if avg_sentiment >= 0.70:
            return "Highly Healthy"
        elif avg_sentiment >= 0.55:
            return "Healthy"
        elif avg_sentiment >= 0.40:
            return "Moderate"
        else:
            return "Challenged"
    
    def analyze_market_share(self) -> Dict:
        """Estimate market share distribution."""
        logger.info("Analyzing market share distribution...")
        
        share_analysis = {
            "by_sector": {},
            "top_players": [],
            "concentration_index": 0.0
        }
        
        # Calculate market share estimates based on sentiment and company data
        for sector, landscape in self.analysis["competitive_landscape"]["sector_breakdown"].items():
            companies = landscape.get("companies", [])
            
            # Simplified market share calculation
            # In production: use actual revenue, contract value, etc.
            total_score = sum(c["sentiment_score"] for c in companies)
            
            sector_shares = []
            for company in companies:
                share_pct = (company["sentiment_score"] / total_score * 100) if total_score > 0 else 0
                sector_shares.append({
                    "company": company["name"],
                    "estimated_share": round(share_pct, 2),
                    "position": company["market_position"]
                })
            
            share_analysis["by_sector"][sector] = sorted(
                sector_shares,
                key=lambda x: x["estimated_share"],
                reverse=True
            )
        
        self.analysis["market_share_analysis"] = share_analysis
        return share_analysis
    
    def analyze_sentiment_trends(self) -> Dict:
        """Aggregate and analyze market sentiment."""
        logger.info("Analyzing sentiment trends...")
        
        sentiment_summary = {
            "overall_market_sentiment": 0.0,
            "sentiment_by_sector": {},
            "positive_momentum": [],
            "negative_momentum": [],
            "sentiment_distribution": {
                "very_positive": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "very_negative": 0
            }
        }
        
        all_sentiments = []
        
        for sector, landscape in self.analysis["competitive_landscape"]["sector_breakdown"].items():
            companies = landscape.get("companies", [])
            sector_sentiments = [c["sentiment_score"] for c in companies]
            
            if sector_sentiments:
                avg_sentiment = np.mean(sector_sentiments)
                sentiment_summary["sentiment_by_sector"][sector] = {
                    "average": round(avg_sentiment, 3),
                    "trend": self._determine_trend(avg_sentiment)
                }
                all_sentiments.extend(sector_sentiments)
                
                # Identify momentum players
                for company in companies:
                    score = company["sentiment_score"]
                    if score >= 0.75:
                        sentiment_summary["positive_momentum"].append(company["name"])
                    elif score <= 0.35:
                        sentiment_summary["negative_momentum"].append(company["name"])
        
        # Overall market sentiment
        if all_sentiments:
            sentiment_summary["overall_market_sentiment"] = round(np.mean(all_sentiments), 3)
            
            # Distribution
            for score in all_sentiments:
                if score >= 0.80:
                    sentiment_summary["sentiment_distribution"]["very_positive"] += 1
                elif score >= 0.60:
                    sentiment_summary["sentiment_distribution"]["positive"] += 1
                elif score >= 0.40:
                    sentiment_summary["sentiment_distribution"]["neutral"] += 1
                elif score >= 0.20:
                    sentiment_summary["sentiment_distribution"]["negative"] += 1
                else:
                    sentiment_summary["sentiment_distribution"]["very_negative"] += 1
        
        self.analysis["sentiment_analysis"] = sentiment_summary
        return sentiment_summary
    
    def _determine_trend(self, sentiment: float) -> str:
        """Determine trend direction."""
        if sentiment >= 0.65:
            return "Bullish"
        elif sentiment >= 0.45:
            return "Stable"
        else:
            return "Bearish"
    
    def analyze_growth_indicators(self) -> Dict:
        """Analyze growth indicators and market expansion."""
        logger.info("Analyzing growth indicators...")
        
        growth_metrics = {
            "high_growth_sectors": [],
            "stable_sectors": [],
            "contracting_sectors": [],
            "innovation_index": {},
            "market_expansion_opportunities": []
        }
        
        # Analyze sector growth potential
        for sector, landscape in self.analysis["competitive_landscape"]["sector_breakdown"].items():
            avg_sentiment = landscape["average_sentiment"]
            company_count = landscape["company_count"]
            
            growth_score = avg_sentiment * (1 + np.log1p(company_count) / 10)
            
            sector_profile = {
                "sector": sector,
                "growth_score": round(growth_score, 3),
                "company_count": company_count,
                "health": landscape["sector_health"]
            }
            
            if growth_score >= 0.70:
                growth_metrics["high_growth_sectors"].append(sector_profile)
            elif growth_score >= 0.50:
                growth_metrics["stable_sectors"].append(sector_profile)
            else:
                growth_metrics["contracting_sectors"].append(sector_profile)
            
            # Innovation index
            growth_metrics["innovation_index"][sector] = round(growth_score * 100, 2)
        
        # Market expansion opportunities
        if growth_metrics["high_growth_sectors"]:
            growth_metrics["market_expansion_opportunities"] = [
                f"Expand presence in {sector['sector']}" 
                for sector in growth_metrics["high_growth_sectors"][:3]
            ]
        
        self.analysis["growth_indicators"] = growth_metrics
        return growth_metrics
    
    def assess_market_risks(self) -> Dict:
        """Assess market risks and challenges."""
        logger.info("Assessing market risks...")
        
        risk_profile = {
            "overall_risk_level": "moderate",
            "sector_risks": {},
            "competitive_threats": [],
            "market_vulnerabilities": [],
            "mitigation_strategies": []
        }
        
        high_risk_count = 0
        
        for sector, landscape in self.analysis["competitive_landscape"]["sector_breakdown"].items():
            avg_sentiment = landscape["average_sentiment"]
            sentiment_std = landscape.get("sentiment_std", 0.1)
            
            # Risk calculation
            risk_score = (1 - avg_sentiment) + sentiment_std
            
            if risk_score >= 0.70:
                risk_level = "High"
                high_risk_count += 1
                risk_profile["competitive_threats"].append(
                    f"{sector}: High volatility detected"
                )
            elif risk_score >= 0.45:
                risk_level = "Moderate"
            else:
                risk_level = "Low"
            
            risk_profile["sector_risks"][sector] = {
                "risk_level": risk_level,
                "risk_score": round(risk_score, 3),
                "volatility": round(sentiment_std, 3)
            }
        
        # Overall risk assessment
        if high_risk_count >= 2:
            risk_profile["overall_risk_level"] = "elevated"
        elif high_risk_count == 0:
            risk_profile["overall_risk_level"] = "low"
        
        # Mitigation strategies
        risk_profile["mitigation_strategies"] = [
            "Diversify across multiple aerospace sectors",
            "Monitor government contract pipeline",
            "Track technological disruptions",
            "Maintain strong competitive positioning"
        ]
        
        self.analysis["risk_assessment"] = risk_profile
        return risk_profile
    
    def generate_strategic_insights(self) -> List[str]:
        """Generate actionable strategic insights."""
        logger.info("Generating strategic insights...")
        
        insights = []
        
        # Insight 1: Market leaders
        leaders = self.analysis["competitive_landscape"].get("market_leaders", [])
        if leaders:
            top_leader = leaders[0]["name"]
            insights.append(
                f"Market Leadership: {top_leader} maintains dominant position with strong sentiment metrics"
            )
        
        # Insight 2: Growth sectors
        high_growth = self.analysis["growth_indicators"].get("high_growth_sectors", [])
        if high_growth:
            growth_sector = high_growth[0]["sector"]
            insights.append(
                f"Growth Opportunity: {growth_sector} sector shows highest growth potential"
            )
        
        # Insight 3: Risk areas
        risk_level = self.analysis["risk_assessment"]["overall_risk_level"]
        insights.append(
            f"Risk Assessment: Market risk level assessed as {risk_level.upper()}"
        )
        
        # Insight 4: Sentiment trend
        overall_sentiment = self.analysis["sentiment_analysis"]["overall_market_sentiment"]
        if overall_sentiment >= 0.65:
            insights.append(
                "Market Sentiment: Strong positive momentum across aerospace sector"
            )
        elif overall_sentiment <= 0.45:
            insights.append(
                "Market Sentiment: Caution advised due to negative sentiment trends"
            )
        
        # Insight 5: Competitive dynamics
        sector_count = len(self.analysis["competitive_landscape"]["sector_breakdown"])
        insights.append(
            f"Market Structure: {sector_count} distinct aerospace sectors identified with varying dynamics"
        )
        
        self.analysis["strategic_insights"] = insights
        return insights
    
    def run_full_analysis(self) -> Dict:
        """Execute complete market analysis pipeline."""
        logger.info("=" * 70)
        logger.info("Starting Clearglassinc Market Analysis")
        logger.info(f"Version: {__version__}")
        logger.info("=" * 70)
        
        # Run all analysis modules
        self.analyze_competitive_landscape()
        self.analyze_market_share()
        self.analyze_sentiment_trends()
        self.analyze_growth_indicators()
        self.assess_market_risks()
        self.generate_strategic_insights()
        
        logger.info("=" * 70)
        logger.info("Market analysis completed")
        logger.info(f"Strategic insights generated: {len(self.analysis['strategic_insights'])}")
        logger.info("=" * 70)
        
        return self.analysis

# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=f"Clearglassinc Market Analyzer v{__version__}",
        epilog=__copyright__
    )
    parser.add_argument("--input", required=True, help="Input data file (JSON)")
    parser.add_argument("--output", required=True, help="Output analysis file (JSON)")
    
    args = parser.parse_args()
    
    # Load data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    # Run analysis
    analyzer = ClearglassMarketAnalyzer(data)
    analysis = analyzer.run_full_analysis()
    
    # Save results
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"Analysis saved to: {args.output}")
    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")
        sys.exit(1)
    
    # Print key insights
    logger.info("\nKEY STRATEGIC INSIGHTS:")
    for i, insight in enumerate(analysis["strategic_insights"], 1):
        logger.info(f"  {i}. {insight}")
    
    logger.info(f"\n{__copyright__}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

# End of Clearglassinc Market Analyzer
# © 2025-2030 Clearglassinc. All Rights Reserved.
