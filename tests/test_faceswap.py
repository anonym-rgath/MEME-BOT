from memebot.faceswap.provider import ReplicateProvider

class FakeReplicate:
    def __init__(self, output):
        self._output = output
        self.calls = []
    def run(self, model, input):
        self.calls.append((model, input))
        return self._output

def test_swap_image_passes_model_and_returns_url(tmp_path):
    fake = FakeReplicate(output="https://result/out.jpg")
    prov = ReplicateProvider(
        client=fake, image_model="org/img", video_model="org/vid",
    )
    target = tmp_path / "target.jpg"; target.write_bytes(b"t")
    face = tmp_path / "face.jpg"; face.write_bytes(b"f")

    url = prov.swap_image(str(target), str(face))

    assert url == "https://result/out.jpg"
    assert fake.calls[0][0] == "org/img"
    # both files were opened and passed as input
    assert set(fake.calls[0][1].keys()) >= {"input_image", "swap_image"}

def test_swap_video_uses_video_model(tmp_path):
    fake = FakeReplicate(output="https://result/out.mp4")
    prov = ReplicateProvider(
        client=fake, image_model="org/img", video_model="org/vid",
    )
    target = tmp_path / "t.mp4"; target.write_bytes(b"t")
    face = tmp_path / "f.jpg"; face.write_bytes(b"f")

    url = prov.swap_video(str(target), str(face))

    assert url == "https://result/out.mp4"
    assert fake.calls[0][0] == "org/vid"

def test_list_output_returns_first(tmp_path):
    fake = FakeReplicate(output=["https://a", "https://b"])
    prov = ReplicateProvider(client=fake, image_model="m", video_model="v")
    t = tmp_path / "t.jpg"; t.write_bytes(b"t")
    f = tmp_path / "f.jpg"; f.write_bytes(b"f")
    assert prov.swap_image(str(t), str(f)) == "https://a"
