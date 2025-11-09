import matplotlib.pyplot as plt
import pandas as pd

import src.utils as utils


def test_save_dataframe_and_plot(tmp_path, monkeypatch):
    monkeypatch.setattr(utils, "REPORTS_DIR", tmp_path)

    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    csv_path = utils.save_dataframe(df, "sample.csv", ticker="TST")
    assert csv_path.exists()
    assert csv_path.parent == tmp_path / "TST"

    fig = plt.figure()
    png_path = utils.save_plot("sample.png", ticker="TST", fig=fig)
    assert png_path.exists()
