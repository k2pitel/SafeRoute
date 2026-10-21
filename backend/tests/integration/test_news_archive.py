"""services/news -> datalag.news_archive against a throwaway SQLite file."""
from datetime import UTC, datetime

from app.datalag import news_archive
from app.shared.news import NewsItem


def test_archive_dedupes_by_url(tmp_stores):
    published = datetime(2024, 5, 1, tzinfo=UTC)
    item = NewsItem(title="Røveri i Aarhus", url="https://x.dk/1", source="Test", published_at=published)
    assert news_archive.save_items([item]) == 1
    assert news_archive.save_items([item]) == 0
    assert news_archive.count() == 1


def test_archive_year_filter(tmp_stores):
    def item(url, year):
        published = datetime(year, 6, 1, tzinfo=UTC)
        return NewsItem(title=f"Vold {year}", url=url, source="T", published_at=published)

    news_archive.save_items([item("u1", 2021), item("u2", 2024)])
    assert [i.url for i in news_archive.load_items(year=2021)] == ["u1"]
