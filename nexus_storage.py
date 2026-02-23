"""
NEXUS Persistent Storage Layer
Handles all file-based data persistence for the trading bot.
Saves to ./nexus_data/ directory alongside the main script.
"""

import os
import json
import csv
import shutil
import hashlib
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Data directory setup ──────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent / "nexus_data"
DIRS = {
    "root":        BASE_DIR,
    "scans":       BASE_DIR / "scans",
    "simulations": BASE_DIR / "simulations",
    "trades":      BASE_DIR / "trades",
    "alerts":      BASE_DIR / "alerts",
    "config":      BASE_DIR / "config",
    "ai_log":      BASE_DIR / "ai_log",
    "snapshots":   BASE_DIR / "snapshots",
}

def ensure_dirs():
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)

ensure_dirs()

# ── Timestamp helpers ─────────────────────────────────────────────────────────
def now_str()  -> str: return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
def now_tag()  -> str: return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
def today_str()-> str: return datetime.utcnow().strftime("%Y-%m-%d")

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG / SETTINGS  (API keys, strategy params, preferences)
# ─────────────────────────────────────────────────────────────────────────────
CONFIG_FILE = DIRS["config"] / "settings.json"

def load_config() -> dict:
    """Load persisted app config. Returns empty dict if not found."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(data: dict):
    """Save app config. API secret is stored but masked in display."""
    ensure_dirs()
    # Never store raw secret on disk — store a hash for verification only
    safe = dict(data)
    if "api_secret" in safe and safe["api_secret"]:
        safe["api_secret_hash"] = hashlib.sha256(safe["api_secret"].encode()).hexdigest()[:16]
        safe["api_secret"] = "***STORED***"   # Don't persist the actual secret
    if "api_passphrase" in safe and safe["api_passphrase"]:
        safe["api_passphrase"] = "***STORED***"
    with open(CONFIG_FILE, "w") as f:
        json.dump({**safe, "_saved": now_str()}, f, indent=2)

PARAMS_FILE = DIRS["config"] / "strategy_params.json"

def load_strategy_params() -> dict:
    try:
        if PARAMS_FILE.exists():
            with open(PARAMS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_strategy_params(params: dict):
    ensure_dirs()
    with open(PARAMS_FILE, "w") as f:
        json.dump({**params, "_saved": now_str()}, f, indent=2)

# ─────────────────────────────────────────────────────────────────────────────
# SCAN RESULTS
# ─────────────────────────────────────────────────────────────────────────────
def save_scan(df: pd.DataFrame, scan_number: int):
    """Save scan results as CSV + append summary to master log."""
    ensure_dirs()
    tag = now_tag()

    # Individual scan CSV
    csv_path = DIRS["scans"] / f"scan_{scan_number:04d}_{tag}.csv"
    df.to_csv(csv_path, index=False)

    # Master scan log (append)
    master = DIRS["scans"] / "scan_history.csv"
    row = {
        "scan_number": scan_number,
        "timestamp": now_str(),
        "total_signals": len(df),
        "buy_signals":  len(df[df["Signal"]=="BUY"]),
        "sell_signals": len(df[df["Signal"]=="SELL"]),
        "coins_scanned": df["Coin"].nunique() if "Coin" in df.columns else 0,
        "avg_confidence": round(df["Confidence"].mean(), 1) if "Confidence" in df.columns else 0,
        "file": csv_path.name,
    }
    write_header = not master.exists()
    with open(master, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if write_header: w.writeheader()
        w.writerow(row)

    return str(csv_path)

def load_scan_history() -> pd.DataFrame:
    master = DIRS["scans"] / "scan_history.csv"
    if master.exists():
        try:
            return pd.read_csv(master)
        except Exception:
            pass
    return pd.DataFrame()

def list_saved_scans() -> List[Path]:
    return sorted(DIRS["scans"].glob("scan_*.csv"), reverse=True)[:20]

def load_saved_scan(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION RESULTS
# ─────────────────────────────────────────────────────────────────────────────
def save_simulation(results: dict, sim_number: int):
    """Save full simulation data as JSON + trade log as CSV."""
    ensure_dirs()
    tag = now_tag()
    strat_slug = results.get("strategy", "unknown").replace("/","").replace(" ","_")[:20]
    base_name  = f"sim_{sim_number:04d}_{strat_slug}_{tag}"

    # Full JSON (equity curve + metadata)
    json_path = DIRS["simulations"] / f"{base_name}.json"
    save_data = {
        "strategy":      results.get("strategy",""),
        "capital":       results.get("capital", 0),
        "final_balance": results.get("final", 0),
        "total_return":  results.get("total_ret", 0),
        "win_rate":      results.get("win_rate", 0),
        "trade_count":   results.get("trades", 0),
        "avg_win":       results.get("avg_win", 0),
        "avg_loss":      results.get("avg_loss", 0),
        "profit_factor": results.get("profit_factor", 0),
        "max_drawdown":  results.get("max_dd", 0),
        "sharpe":        results.get("sharpe", 0),
        "equity_curve":  results.get("equity", []),
        "timestamp":     now_str(),
    }
    with open(json_path, "w") as f:
        json.dump(save_data, f, indent=2)

    # Trade log CSV
    if results.get("trade_log"):
        trades_path = DIRS["simulations"] / f"{base_name}_trades.csv"
        pd.DataFrame(results["trade_log"]).to_csv(trades_path, index=False)

    # Master simulation log
    master = DIRS["simulations"] / "simulation_history.csv"
    row = {
        "sim_number":    sim_number,
        "timestamp":     now_str(),
        "strategy":      results.get("strategy",""),
        "capital":       results.get("capital", 0),
        "final_balance": results.get("final", 0),
        "total_return":  results.get("total_ret", 0),
        "win_rate":      results.get("win_rate", 0),
        "trades":        results.get("trades", 0),
        "profit_factor": results.get("profit_factor", 0),
        "max_dd":        results.get("max_dd", 0),
        "sharpe":        results.get("sharpe", 0),
        "file":          json_path.name,
    }
    write_header = not master.exists()
    with open(master, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if write_header: w.writeheader()
        w.writerow(row)

    return str(json_path)

def load_simulation_history() -> pd.DataFrame:
    master = DIRS["simulations"] / "simulation_history.csv"
    if master.exists():
        try:
            return pd.read_csv(master)
        except Exception:
            pass
    return pd.DataFrame()

def load_simulation_detail(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}

def list_saved_simulations() -> List[Path]:
    return sorted(DIRS["simulations"].glob("sim_*.json"), reverse=True)[:30]

# ─────────────────────────────────────────────────────────────────────────────
# ALERTS LOG
# ─────────────────────────────────────────────────────────────────────────────
ALERTS_FILE = DIRS["alerts"] / "alerts.json"

def save_alerts(alerts: list):
    """Persist alert list to JSON (keep last 200)."""
    ensure_dirs()
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts[:200], f, indent=2)

def load_alerts() -> list:
    try:
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def append_alert(alert: dict):
    """Fast append to alert log file."""
    ensure_dirs()
    alerts = load_alerts()
    alerts.insert(0, alert)
    save_alerts(alerts)

# ─────────────────────────────────────────────────────────────────────────────
# AI PARAMETER LOG
# ─────────────────────────────────────────────────────────────────────────────
AI_LOG_FILE = DIRS["ai_log"] / "ai_updates.json"

def save_ai_log(log: list):
    ensure_dirs()
    with open(AI_LOG_FILE, "w") as f:
        json.dump(log[:500], f, indent=2)

def load_ai_log() -> list:
    try:
        if AI_LOG_FILE.exists():
            with open(AI_LOG_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def append_ai_log(entry: dict):
    log = load_ai_log()
    log.insert(0, entry)
    save_ai_log(log)

    # Also write to daily CSV for analysis
    csv_path = DIRS["ai_log"] / f"ai_log_{today_str()}.csv"
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["time","strat","msg"])
        if write_header: w.writeheader()
        w.writerow(entry)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION SNAPSHOT  (full state backup / restore)
# ─────────────────────────────────────────────────────────────────────────────
def save_snapshot(session_data: dict):
    """Save a complete session snapshot for crash recovery."""
    ensure_dirs()
    snap_path = DIRS["snapshots"] / f"snapshot_{now_tag()}.json"

    # Keep only serialisable primitive data (no DataFrames, no plotly figs)
    safe = {}
    for k, v in session_data.items():
        if isinstance(v, (str, int, float, bool, list, dict, type(None))):
            safe[k] = v
    safe["_snapshot_time"] = now_str()

    with open(snap_path, "w") as f:
        json.dump(safe, f, indent=2)

    # Keep only last 5 snapshots
    snaps = sorted(DIRS["snapshots"].glob("snapshot_*.json"))
    for old in snaps[:-5]:
        old.unlink(missing_ok=True)

    return str(snap_path)

def load_latest_snapshot() -> dict:
    snaps = sorted(DIRS["snapshots"].glob("snapshot_*.json"))
    if snaps:
        try:
            with open(snaps[-1]) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# ─────────────────────────────────────────────────────────────────────────────
# TRADE JOURNAL  (manual or auto-logged paper trades)
# ─────────────────────────────────────────────────────────────────────────────
JOURNAL_FILE = DIRS["trades"] / "trade_journal.csv"

JOURNAL_FIELDS = [
    "id","timestamp","source","strategy","coin","interval",
    "side","entry_price","exit_price","quantity","pnl_pct",
    "pnl_usdt","reason","tags","notes",
]

def log_trade(trade: dict):
    """Append a trade to the journal."""
    ensure_dirs()
    write_header = not JOURNAL_FILE.exists()
    row = {f: trade.get(f, "") for f in JOURNAL_FIELDS}
    if not row["timestamp"]: row["timestamp"] = now_str()
    if not row["id"]: row["id"] = now_tag()
    with open(JOURNAL_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=JOURNAL_FIELDS)
        if write_header: w.writeheader()
        w.writerow(row)

def load_trade_journal() -> pd.DataFrame:
    if JOURNAL_FILE.exists():
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception:
            pass
    return pd.DataFrame(columns=JOURNAL_FIELDS)

def bulk_log_simulation_trades(sim_results: dict, sim_number: int):
    """Auto-log all trades from a simulation into the journal."""
    strat = sim_results.get("strategy","unknown")
    for t in sim_results.get("trade_log", []):
        if t.get("type") == "SELL":
            log_trade({
                "source":       f"SIM#{sim_number}",
                "strategy":     strat,
                "coin":         "BTC/USDT",
                "side":         t["type"],
                "entry_price":  "",
                "exit_price":   round(t["price"], 4),
                "pnl_pct":      t.get("pnl", 0),
                "pnl_usdt":     round(sim_results.get("capital",10000) * t.get("pnl",0)/100, 2),
                "reason":       t.get("reason",""),
                "tags":         "simulation",
            })

# ─────────────────────────────────────────────────────────────────────────────
# DATA EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def export_all_to_zip() -> Path:
    """Zip the entire nexus_data directory for download."""
    zip_path = Path(__file__).parent / "nexus_export"
    shutil.make_archive(str(zip_path), "zip", BASE_DIR)
    return Path(str(zip_path) + ".zip")

# ─────────────────────────────────────────────────────────────────────────────
# STORAGE STATS
# ─────────────────────────────────────────────────────────────────────────────
def get_storage_stats() -> dict:
    stats = {"total_size_kb": 0, "file_counts": {}}
    for name, d in DIRS.items():
        if name == "root": continue
        files = list(d.glob("*")) if d.exists() else []
        size = sum(f.stat().st_size for f in files if f.is_file())
        stats["file_counts"][name] = len(files)
        stats["total_size_kb"] += size
    stats["total_size_kb"] = round(stats["total_size_kb"] / 1024, 1)
    return stats
