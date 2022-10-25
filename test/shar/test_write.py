import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from lhotse import CutSet
from lhotse.shar import SharWriter, TarWriter
from lhotse.testing.dummies import DummyManifest


def test_tar_writer(tmp_path: Path):
    with TarWriter(str(tmp_path / "test.%06d.tar"), shard_size=10) as writer:
        writer.write("test.txt", BytesIO(b"test"))

    with tarfile.open(tmp_path / "test.000000.tar") as f:
        f2 = f.extractfile(f.getmember("test.txt"))
        assert f2.read() == b"test"


def test_tar_writer_pipe(tmp_path: Path):
    with TarWriter(f"pipe:cat > {tmp_path}/test.%06d.tar", shard_size=10) as writer:
        writer.write("test.txt", BytesIO(b"test"))

    with tarfile.open(tmp_path / "test.000000.tar") as f:
        f2 = f.extractfile(f.getmember("test.txt"))
        assert f2.read() == b"test"


def test_shar_writer(tmp_path: Path):
    # Prepare data
    cuts = DummyManifest(CutSet, begin_id=0, end_id=20, with_data=True)

    # Prepare system under test
    writer = SharWriter(
        tmp_path,
        fields={
            "recording": "wav",
            "features": "lilcom",
            "custom_embedding": "numpy",
            "custom_features": "lilcom",
            "custom_indexes": "numpy",
            "custom_recording": "wav",
        },
        shard_size=10,
    )

    # Actual test
    with writer:
        for c in cuts:
            writer.write(c)

    # Post-conditions

    # - we created 2 shards with cutsets and a separate file for each data field
    for fname in (
        "cuts.000000.jsonl.gz",
        "cuts.000001.jsonl.gz",
        "recording.000000.tar",
        "recording.000001.tar",
        "features.000000.tar",
        "features.000001.tar",
        "custom_embedding.000000.tar",
        "custom_embedding.000001.tar",
        "custom_features.000000.tar",
        "custom_features.000001.tar",
        "custom_indexes.000000.tar",
        "custom_indexes.000001.tar",
        "custom_recording.000000.tar",
        "custom_recording.000001.tar",
    ):
        assert (tmp_path / fname).is_file()

    # - we didn't create a third shard
    assert not (tmp_path / "cuts.000002.jsonl.gz").exists()

    # - the cuts do not have any data actually attached to them,
    #   so it's impossible to load it if we open it as a normal CutSet
    for cut in CutSet.from_file(tmp_path / "cuts.000000.jsonl.gz"):
        assert cut.recording.sources[0].type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_audio()

        assert cut.features.storage_type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_features()

        assert cut.custom_embedding.storage_type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_custom_embedding()

        assert cut.custom_features.array.storage_type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_custom_features()

        assert cut.custom_indexes.array.storage_type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_custom_indexes()

        assert cut.custom_recording.sources[0].type == "shar"
        with pytest.raises(RuntimeError):
            cut.load_custom_recording()


def test_shar_writer_pipe(tmp_path: Path):
    # Prepare data
    cuts = DummyManifest(CutSet, begin_id=0, end_id=20, with_data=True)

    # Prepare system under test
    writer = SharWriter(
        f"pipe:cat >{tmp_path}",
        fields={
            "recording": "wav",
            "features": "lilcom",
            "custom_embedding": "numpy",
            "custom_features": "lilcom",
            "custom_indexes": "numpy",
            "custom_recording": "wav",
        },
        shard_size=10,
    )

    # Actual test
    with writer:
        for c in cuts:
            writer.write(c)

    # Post-conditions

    # - we created 2 shards with cutsets and a separate file for each data field
    for fname in (
        "cuts.000000.jsonl.gz",
        "cuts.000001.jsonl.gz",
        "recording.000000.tar",
        "recording.000001.tar",
        "features.000000.tar",
        "features.000001.tar",
        "custom_embedding.000000.tar",
        "custom_embedding.000001.tar",
        "custom_features.000000.tar",
        "custom_features.000001.tar",
        "custom_indexes.000000.tar",
        "custom_indexes.000001.tar",
        "custom_recording.000000.tar",
        "custom_recording.000001.tar",
    ):
        assert (tmp_path / fname).is_file()
