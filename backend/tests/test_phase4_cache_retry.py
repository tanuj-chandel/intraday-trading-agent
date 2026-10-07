import pytest
import asyncio
from app.data.adapters.cache_manager import DataCacheManager

@pytest.mark.asyncio
async def test_cache_ttl():
    DataCacheManager.clear()
    DataCacheManager.set("TEST_KEY", "SAMPLE_VAL", ttl_seconds=1.0)
    assert DataCacheManager.get("TEST_KEY") == "SAMPLE_VAL"

    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    assert DataCacheManager.get("TEST_KEY") is None

@pytest.mark.asyncio
async def test_exponential_backoff_retry():
    call_count = 0

    async def flaky_fetch():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Transient network timeout")
        return "SUCCESS_DATA"

    result = await DataCacheManager.fetch_with_retry(flaky_fetch, max_retries=3, base_backoff_seconds=0.05)
    assert result == "SUCCESS_DATA"
    assert call_count == 3
