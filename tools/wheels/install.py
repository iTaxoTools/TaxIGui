import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

import yaml


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()


def verify_file(file_path, expected_hash):
    calculated_hash = calculate_sha256(file_path)
    return calculated_hash == expected_hash


def download_file(egg, url, tmp_dir: Path):
    with urlopen(url) as response:
        if response.getcode() == 200:
            file_name = Path(url).name
            file_path = tmp_dir / file_name
            with open(file_path, "wb") as file:
                file.write(response.read())
            return file_path
        else:
            raise Exception(
                f"Failed to download wheel for egg: {egg}. HTTP status code: {response.getcode()}"
            )


def download_wheel(wheel: dict, tmp_dir: Path):
    egg = wheel["egg"]
    url = wheel["url"]
    hash = wheel["sha256"]

    print(f"Downloading wheel for {egg}...")
    file_path = download_file(egg, url, tmp_dir)
    if not verify_file(file_path, hash):
        raise Exception(f"Wheel hash does not match for: {egg}")


def download_wheels(wheels: list[dict], tmp_dir: Path):
    for wheel in wheels:
        download_wheel(wheel, tmp_dir)


def install_all(tmp_dir: Path):
    wheels = list(tmp_dir.glob("*.whl"))
    cmd = [sys.executable, "-m", "pip", "install"]
    cmd.extend(str(wheel) for wheel in wheels)
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def main(path: str):
    with open(path) as file:
        text = file.read()

    wheels = yaml.safe_load(text)

    with tempfile.TemporaryDirectory() as tmp_dir:
        download_wheels(wheels, Path(tmp_dir))
        install_all(Path(tmp_dir))


if __name__ == "__main__":
    path = Path(sys.argv[1])
    main(path)
