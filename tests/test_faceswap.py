from memebot.faceswap.provider import ReplicateProvider

class FakeReplicate:
    def __init__(self, output):
        self._output = output
        self.calls = []
    def run(self, model, input):
        self.calls.append((model, input))
        return self._output

def _provider(fake, **kw):
    return ReplicateProvider(
        client=fake, image_model="org/img", video_model="org/vid",
        faceswap_prompt="swap the faces", **kw,
    )

def test_swap_image_sends_prompt_and_two_images(tmp_path):
    fake = FakeReplicate(output="https://result/out.jpg")
    prov = _provider(fake)
    target = tmp_path / "target.jpg"; target.write_bytes(b"t")
    face = tmp_path / "face.jpg"; face.write_bytes(b"f")

    url = prov.swap_image(str(target), str(face))

    assert url == "https://result/out.jpg"
    assert fake.calls[0][0] == "org/img"
    inp = fake.calls[0][1]
    assert inp["prompt"] == "swap the faces"
    assert len(inp["image_input"]) == 2  # target + face passed as an array

def test_swap_image_respects_custom_images_key(tmp_path):
    fake = FakeReplicate(output="https://result/out.jpg")
    prov = _provider(fake, images_key="image_urls")
    target = tmp_path / "t.jpg"; target.write_bytes(b"t")
    face = tmp_path / "f.jpg"; face.write_bytes(b"f")

    prov.swap_image(str(target), str(face))

    assert "image_urls" in fake.calls[0][1]
    assert len(fake.calls[0][1]["image_urls"]) == 2

def test_swap_video_uses_video_model_and_legacy_keys(tmp_path):
    fake = FakeReplicate(output="https://result/out.mp4")
    prov = _provider(fake)
    target = tmp_path / "t.mp4"; target.write_bytes(b"t")
    face = tmp_path / "f.jpg"; face.write_bytes(b"f")

    url = prov.swap_video(str(target), str(face))

    assert url == "https://result/out.mp4"
    assert fake.calls[0][0] == "org/vid"
    assert set(fake.calls[0][1].keys()) >= {"input_image", "swap_image"}

def test_list_output_returns_first(tmp_path):
    fake = FakeReplicate(output=["https://a", "https://b"])
    prov = _provider(fake)
    t = tmp_path / "t.jpg"; t.write_bytes(b"t")
    f = tmp_path / "f.jpg"; f.write_bytes(b"f")
    assert prov.swap_image(str(t), str(f)) == "https://a"
