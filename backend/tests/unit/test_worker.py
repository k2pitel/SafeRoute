"""Async Worker (worker/) and the zone_updates broker."""
import asyncio

import pytest

from app.api.zones import updates as zone_updates
from app.shared.geo import BBox
from app.worker import jobs
from app.worker.background import BackgroundAsyncWorker
from app.worker.factory import create_async_worker

AREA = BBox(10.1, 56.1, 10.2, 56.2)


def test_factory_picks_realisation():
    assert isinstance(create_async_worker("background"), BackgroundAsyncWorker)
    assert type(create_async_worker("celery")).__name__ == "CeleryAsyncWorker"
    with pytest.raises(ValueError):
        create_async_worker("cron")


def test_event_triggered_job_submitted_before_start_runs_after_start(monkeypatch):
    seen = []

    async def fake_recalculate(area=None):
        seen.append(area)

    monkeypatch.setattr(jobs, "recalculate_segment_scores", fake_recalculate)

    async def scenario():
        worker = BackgroundAsyncWorker(periodic_jobs=[])
        worker.submit_recalculation(AREA)  # API may enqueue before lifespan starts the worker
        await worker.start()
        worker.submit_recalculation(BBox(0, 0, 1, 1))
        await asyncio.sleep(0.05)
        await worker.stop()

    asyncio.run(scenario())
    assert seen == [AREA, BBox(0, 0, 1, 1)]


def test_failing_periodic_job_does_not_stop_the_worker():
    calls = []

    async def flaky():
        calls.append(1)
        raise RuntimeError("source down")

    async def scenario():
        worker = BackgroundAsyncWorker(periodic_jobs=[("flaky", 0.01, flaky)])
        await worker.start()
        await asyncio.sleep(0.1)
        await worker.stop()

    asyncio.run(scenario())
    assert len(calls) > 1  # retried on the next interval (NF7)


def test_broker_fans_out_and_unsubscribes():
    async def scenario():
        async with zone_updates.subscribe() as a, zone_updates.subscribe() as b:
            zone_updates.publish({"type": "x"})
            assert (await a.get(), await b.get()) == ({"type": "x"}, {"type": "x"})
        assert zone_updates.subscriber_count() == 0

    asyncio.run(scenario())


def test_refresh_crime_stats_publishes_zone_event(monkeypatch):
    async def fake_refresh():
        return 7

    monkeypatch.setattr(jobs.crime_stats, "refresh_cache", fake_refresh)

    async def scenario():
        async with zone_updates.subscribe() as events:
            await jobs.refresh_crime_stats()
            return await events.get()

    event = asyncio.run(scenario())
    assert event["type"] == "zones_refreshed" and event["zones_cached"] == 7
