from memebot.replicate_io import first_url

class _Obj:
    def __init__(self, url): self.url = url

def test_first_url_str():
    assert first_url("https://a") == "https://a"

def test_first_url_list_takes_first():
    assert first_url(["https://a", "https://b"]) == "https://a"

def test_first_url_object_with_url_attr():
    assert first_url(_Obj("https://x")) == "https://x"
