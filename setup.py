from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).parent.resolve()
README_PATH = BASE_DIR / "README.md"

setup(
    name="django-vert-helper",
    version="1.1.4",
    description="Biblioteca para health checks e acoes operacionais",
    long_description=README_PATH.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    install_requires=[
        "django>=5.2.12, <6.0",
        "djangorestframework>=3.15.2, <4.0",
        "django-filter>=24.3, <26.0",
    ],
    python_requires=">=3.12",
)
