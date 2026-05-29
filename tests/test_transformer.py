"""Tests for ArticleTransformer."""

from src.transformers.article_transformer import ArticleTransformer


def test_transform_hackernews_skips_items_without_url():
    transformer = ArticleTransformer()
    raw = [
        {"title": "Has URL", "url": "http://a.com", "time": 1234567890, "score": 5},
        {"title": "Ask HN: no url", "time": 1234567890},
    ]
    articles = transformer.transform_hackernews(raw)
    assert len(articles) == 1
    assert articles[0].title == "Has URL"
    assert articles[0].source == "hackernews"
    assert articles[0].score == 5


def test_transform_rss_strips_html_and_truncates():
    transformer = ArticleTransformer()
    entries = [
        {
            "title": "RSS Item",
            "link": "http://b.com",
            "published": "2026-01-01T00:00:00Z",
            "summary": "<p>" + "x" * 300 + "</p>",
        }
    ]
    articles = transformer.transform_rss(entries)
    assert len(articles) == 1
    assert articles[0].source == "rss"
    assert "<p>" not in articles[0].summary
    assert len(articles[0].summary) <= 200


def test_transform_rss_skips_entries_without_link():
    transformer = ArticleTransformer()
    assert transformer.transform_rss([{"title": "no link"}]) == []


def test_parse_date_falls_back_to_now():
    transformer = ArticleTransformer()
    # Should not raise on garbage input.
    result = transformer._parse_date("not a date")
    assert result is not None
