from memebot.textremove.provider import ReplicateTextRemover

class FakeReplicate:
    def __init__(self, output):
        self._output = output
        self.calls = []
    def run(self, model, input):
        self.calls.append((model, input))
        return self._output

def test_remove_text_uses_default_keys(tmp_path):
    fake = FakeReplicate(output="https://result/clean.jpg")
    prov = ReplicateTextRemover(client=fake, model="owner/textrm", instruction="remove all the text")
    img = tmp_path / "in.jpg"; img.write_bytes(b"x")

    url = prov.remove_text(str(img))

    assert url == "https://result/clean.jpg"
    assert fake.calls[0][0] == "owner/textrm"
    # defaults match flux-kontext: input_image + prompt
    assert fake.calls[0][1]["prompt"] == "remove all the text"
    assert "input_image" in fake.calls[0][1]

def test_remove_text_respects_custom_keys(tmp_path):
    fake = FakeReplicate(output="https://result/clean.jpg")
    prov = ReplicateTextRemover(
        client=fake, model="m", instruction="x",
        image_key="image", prompt_key="instruction")
    img = tmp_path / "in.jpg"; img.write_bytes(b"x")

    prov.remove_text(str(img))

    assert "image" in fake.calls[0][1]
    assert fake.calls[0][1]["instruction"] == "x"

def test_remove_text_list_output_returns_first(tmp_path):
    fake = FakeReplicate(output=["https://a", "https://b"])
    prov = ReplicateTextRemover(client=fake, model="m", instruction="x")
    img = tmp_path / "in.jpg"; img.write_bytes(b"x")
    assert prov.remove_text(str(img)) == "https://a"
