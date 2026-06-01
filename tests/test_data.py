from src.data import _is_etf, _is_stock, _to_ak_symbol_stock


def test_stock_and_etf_codes_are_classified_separately():
    assert _is_stock("600519.SH")
    assert _is_stock("000001.SZ")
    assert not _is_stock("510300.SH")
    assert not _is_stock("159915.SZ")

    assert _is_etf("510300.SH")
    assert _is_etf("159915.SZ")
    assert not _is_etf("600519.SH")


def test_stock_symbol_is_converted_for_akshare_daily_api():
    assert _to_ak_symbol_stock("600519.SH") == "sh600519"
    assert _to_ak_symbol_stock("000001.SZ") == "sz000001"

