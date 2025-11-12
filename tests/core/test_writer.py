"""Test file writer."""

import re
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pytest
import ratapi

from rascal2.core.writer import write_result_to_zipped_csvs

DATA_PATH = Path(__file__, "../../data/").resolve()


@pytest.mark.parametrize(
    "result_file",
    (
        "results_normal_calculate.json",
        "results_domains_dream.json",
        "results_domains_ns.json",
    ),
)
def test_write_zipped_csv(result_file):
    """Test the plaintext reader successfully reads in data."""

    result = ratapi.Results.load(DATA_PATH / result_file)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp, "project.zip")
        write_result_to_zipped_csvs(zip_path, result)

        assert zip_path.is_file()
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(tmp)
            for name in zip_file.namelist():
                mod_name = name.replace("R_stat", "Rstat")
                name_part = re.sub(r"/|_contrast|_domain|_|.csv", " ", mod_name).split()
                array = np.loadtxt(Path(tmp, name), delimiter=",")

                prop = result
                for part in name_part:
                    if part == "Bayes":
                        continue
                    if part.isdigit():
                        prop = prop[int(part)]
                    else:
                        # underscore should be removed from r_stat
                        part = part if part != "Rstat" else "R_stat"
                        prop = getattr(prop, part)
                if isinstance(prop, list):
                    prop = prop[0]
                if prop.shape[0] == 1:
                    prop = np.ravel(prop)
                if part == "allChains":
                    prop = prop.reshape(-1, array.shape[-1])
                np.testing.assert_array_almost_equal(prop, array, decimal=7)
