#!/usr/bin/env python3
"""
Clearglassinc Aerospace Market Intelligence - Database Initializer
Copyright © 2025-2030 Clearglassinc. All Rights Reserved.

SQLite/PostgreSQL database schema for aerospace market intelligence.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

__version__ = "5.0.0"
__copyright__ = "© 2025-2030 Clearglassinc. All Rights Reserved."

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "../database/clearglassinc_aerospace.db"

def initialize_database():
    """Initialize Clearglassinc aerospace intelligence database."""
    logger.info("Initializing Clearglassinc database...")
    
    # Create database directory
    db_dir = Path(DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            ticker TEXT,
            sector TEXT NOT NULL,
            subsector TEXT,
            headquarters TEXT,
            website TEXT,
            founded_year INTEGER,
            employee_count INTEGER,
            market_cap_usd REAL,
            is_public BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Market data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            data_date DATE NOT NULL,
            sentiment_score REAL,
            stock_price REAL,
            volume INTEGER,
            market_cap REAL,
            revenue_ttm REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            UNIQUE(company_id, data_date)
        )
    """)
    
    # Contracts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            contract_number TEXT UNIQUE,
            agency TEXT,
            contract_value_usd REAL,
            award_date DATE,
            completion_date DATE,
            description TEXT,
            contract_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
    """)
    
    # Analysis results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_date DATE NOT NULL,
            sector TEXT,
            market_sentiment REAL,
            growth_score REAL,
            risk_level TEXT,
            analysis_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_date DATE NOT NULL,
            target_date DATE NOT NULL,
            sector TEXT,
            predicted_index REAL,
            confidence_score REAL,
            scenario TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Data sources log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_collection_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_timestamp TIMESTAMP NOT NULL,
            source_name TEXT NOT NULL,
            data_type TEXT,
            records_collected INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(data_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_company ON contracts(company_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_target ON predictions(target_date)")
    
    conn.commit()
    
    logger.info(f"Database initialized: {DB_PATH}")
    logger.info("Tables created: companies, market_data, contracts, analysis_results, predictions, data_collection_log")
    
    conn.close()
    return True

if __name__ == "__main__":
    initialize_database()
    logger.info(f"{__copyright__}")
