import pathlib
import subprocess

import pytest

from comment_tree.main import create_app
from sql import insert_data


BASE_DIR = pathlib.Path(__file__).parent.parent


@pytest.fixture
def cli(loop, test_client):
    app = create_app(loop)
    return loop.run_until_complete(test_client(app))


@pytest.fixture
def app_db():
    insert_data.main()
    # subprocess.call(
    #     ['python ', (BASE_DIR / 'install.sh').as_posix()],
    #     shell=True,
    #     cwd=BASE_DIR.as_posix()
    # )
