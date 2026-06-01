import os
import re
import pandas as pd
import akshare as ak
from .config import CACHE_DIR, START, END

def _ensure_dir(d): os.makedirs(d, exist_ok=True)
def _csv_path(code: str, cache_dir=CACHE_DIR) -> str:
    _ensure_dir(cache_dir)
    return os.path.join(cache_dir, f"{code}.csv")

def _read_local(path, start, end):
    if not os.path.exists(path): return None
    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    return df.loc[start:end]

def _write_local(path, df): df.to_csv(path)

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    ren = {
        "开盘": "Open", "最高": "High", "最低": "Low", "收盘": "Close",
        "成交量": "Volume", "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume"
    }
    df = df.rename(columns=ren)
    if "Adj Close" not in df.columns:
        df["Adj Close"] = df["Close"]
    keep = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for k in keep:
        if k not in df.columns:
            df[k] = df["Close"]
    df = df[keep]
    df.index.name = "Date"
    return df

def _split_code(code: str) -> tuple[str, str]:
    if not re.match(r"^\d{6}\.(SH|SZ)$", code, re.IGNORECASE):
        raise RuntimeError(f"不识别的代码格式：{code}，请用 6位代码+交易所后缀，例如 600519.SH / 510300.SH")
    num, ex = code.upper().split(".")
    return num, ex

def _is_etf(code: str) -> bool:
    num, ex = _split_code(code)
    return (ex == "SH" and num.startswith(("510", "511", "512", "513", "515", "516", "517", "518", "588"))) or (
        ex == "SZ" and num.startswith("159")
    )

def _is_stock(code: str) -> bool:
    return bool(re.match(r"^\d{6}\.(SH|SZ)$", code, re.IGNORECASE)) and not _is_etf(code)

def _to_ak_symbol_stock(code: str) -> str:
    num, ex = _split_code(code)
    return f"{ex.lower()}{num}"

def _etf_symbol(code: str) -> str:
    num, _ = _split_code(code)
    return num

def get_price(code: str, start=START, end=END, use_cache=True, adjust="qfq", cache_dir=CACHE_DIR) -> pd.DataFrame:

    path = _csv_path(code, cache_dir=cache_dir)
    if use_cache:
        local = _read_local(path, start, end)
        if local is not None:
            return local

    if _is_etf(code):
        symbol = _etf_symbol(code)
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start.replace("-", ""), end_date=(end or "").replace("-", ""))
        df["Date"] = pd.to_datetime(df["日期"])
        df = df.set_index("Date").sort_index()
        norm = _normalize(df)
        _write_local(path, norm)
        return norm.loc[start:end]

    if _is_stock(code):
        symbol = _to_ak_symbol_stock(code)
        df = ak.stock_zh_a_daily(symbol=symbol, adjust=adjust)

        df = df.reset_index().rename(columns={"index": "Date"}) if "index" in df.columns else df
        if "date" in df.columns:
            df["Date"] = pd.to_datetime(df["date"])
        elif "日期" in df.columns:
            df["Date"] = pd.to_datetime(df["日期"])
        else:
            df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        norm = _normalize(df)
        _write_local(path, norm)
        return norm.loc[start:end]

    raise RuntimeError(f"不识别的代码格式：{code}，请用 6位代码+交易所后缀，例如 600519.SH / 510300.SH")

def get_close_series(code: str, **kwargs) -> pd.Series:
    df = get_price(code, **kwargs)
    s = df["Adj Close"].rename(code)
    s.name = code
    return s

def get_panel(codes, **kwargs) -> pd.DataFrame:
    data = []
    for c in codes:
        data.append(get_close_series(c, **kwargs))
    return pd.concat(data, axis=1).dropna(how="all")
