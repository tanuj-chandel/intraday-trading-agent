from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_sqlite_columns():
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(trades)")).fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "indicators_snapshot" not in existing_cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN indicators_snapshot JSON"))
                if "news_rationale" not in existing_cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN news_rationale JSON"))
                if "slippage_incurred" not in existing_cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN slippage_incurred FLOAT DEFAULT 0.0"))
                if "achieved_r" not in existing_cols:
                    conn.execute(text("ALTER TABLE trades ADD COLUMN achieved_r FLOAT"))
                conn.commit()

            # Check trade_signals table
            sig_res = conn.execute(text("PRAGMA table_info(trade_signals)")).fetchall()
            sig_cols = {row[1] for row in sig_res}
            if sig_cols and "reject_reason" not in sig_cols:
                conn.execute(text("ALTER TABLE trade_signals ADD COLUMN reject_reason VARCHAR"))
                conn.commit()
    except Exception:
        pass

ensure_sqlite_columns()

