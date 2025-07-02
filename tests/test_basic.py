import os


def test_readme_exists():
    assert os.path.isfile("README.md")
