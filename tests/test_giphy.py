from memebot.giphy.client import GiphyClient

class FakeFetch:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def __call__(self, url, params):
        self.calls.append((url, params))
        return self.response

def test_search_returns_urls_with_pg13_and_key():
    fake = FakeFetch({"data": [{"images": {"original": {"url": "https://x.gif"}}}]})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.search("cats", count=3) == ["https://x.gif"]
    url, params = fake.calls[0]
    assert "search" in url
    assert params["q"] == "cats"
    assert params["rating"] == "pg-13"
    assert params["api_key"] == "K"

def test_search_empty_returns_empty_list():
    fake = FakeFetch({"data": []})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.search("nope") == []

def test_search_samples_up_to_count_distinct():
    data = {"data": [{"images": {"original": {"url": f"https://{i}.gif"}}}
                     for i in range(10)]}
    fake = FakeFetch(data)
    c = GiphyClient(api_key="K", fetch_json=fake)
    urls = c.search("many", count=3)
    assert len(urls) == 3
    assert len(set(urls)) == 3  # distinct

def test_random_meme_returns_url():
    fake = FakeFetch({"data": {"images": {"original": {"url": "https://r.gif"}}}})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.random_meme() == "https://r.gif"
    url, params = fake.calls[0]
    assert "random" in url
    assert params["tag"] == "meme"
    assert params["rating"] == "pg-13"

def test_random_meme_empty_returns_none():
    fake = FakeFetch({"data": {}})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.random_meme() is None
