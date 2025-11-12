"""
pressure_plot.py
===================

This script demonstrates how to download and visualize equatorial or meridional
pressure slices from the NOAA Geospace model over a user‑defined date range.

The script does the following:

1. Constructs daily directories on the NOMADS server for the provided date range.
2. Scrapes each directory for 2‑D cut‑plane files (either `z0_` for the
   equatorial plane or `y0_` for the noon–midnight meridional plane).
3. Downloads the files one at a time.
4. Uses SpacePy’s `Bats2d` class to load the data.  `Bats2d` automatically
   interprets SWMF/IDL formatted files and returns variables such as
   coordinates and physical quantities.  Pressure is stored under the key
   `'p'`.
5. Plots the pressure slice using Matplotlib, adds a color bar, and shows
   the plot.  Users can customise the plotting routine as needed.

To run this script you will need the following Python packages installed:

* `requests` for HTTP operations;
* `beautifulsoup4` for HTML parsing;
* `spacepy` (with the `pybats` subpackage) for reading SWMF data;
* `matplotlib` for plotting.

Because downloading and plotting multiple frames can take time and consume
memory, the script processes one file at a time.  You can modify the
`download_and_process` function to save plots to disk instead of displaying
them interactively.

NOTE: The Nomads server restricts certain automated downloads.  When running
this script against the live server, you may need to respect any usage
policies.  Consider using an API key or contacting NOAA if you plan on
bulk downloads.

Author: OpenAI ChatGPT
"""

import datetime as _dt
import io
import os
import re
from dataclasses import dataclass
from typing import Iterable, List

import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from spacepy.pybats.bats import Bats2d


_BASE_URL = (
    "https://nomads.ncep.noaa.gov/pub/data/nccf/com/swmf/prod/swmf.{date}/GM/IO2/"
)


@dataclass
class SliceFile:
    """Container describing a 2‑D slice file on the NOMADS server."""

    url: str
    date: _dt.date
    plane: str  # 'z0' or 'y0'
    start_time: str
    end_time: str


def daterange(start: _dt.date, end: _dt.date) -> Iterable[_dt.date]:
    """Generate dates from start to end inclusive."""
    current = start
    one_day = _dt.timedelta(days=1)
    while current <= end:
        yield current
        current += one_day


def list_slice_files(date: _dt.date, plane: str = "z0") -> List[SliceFile]:
    """
    Scrape the NOMADS directory for available 2‑D cut‑plane files on a given date.

    Parameters
    ----------
    date : datetime.date
        The date for which to list files.
    plane : {'z0', 'y0'}
        Which plane to search for.  'z0' corresponds to the equatorial plane and
        'y0' corresponds to the noon–midnight meridional plane.

    Returns
    -------
    List[SliceFile]
        Metadata for each matching file.
    """
    url = _BASE_URL.format(date=date.strftime("%Y%m%d"))
    print(f"Listing files for {date} ({plane}) at {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"Failed to list directory: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    pattern = re.compile(fr"^{plane}_([0-9T]+)_([0-9T]+)$")
    files: List[SliceFile] = []
    for link in soup.find_all("a"):
        name = link.get("href") or ""
        match = pattern.match(name)
        if match:
            start_time, end_time = match.groups()
            files.append(
                SliceFile(
                    url=os.path.join(url, name),
                    date=date,
                    plane=plane,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
    return files


def download_and_process(slice_file: SliceFile, save_dir: str = "./plots") -> None:
    """
    Download a single 2‑D slice file, parse it with SpacePy, and plot pressure.

    Parameters
    ----------
    slice_file : SliceFile
        Metadata describing the file to download.
    save_dir : str, optional
        Directory in which to save figures.  If None, the plots will be shown
        interactively.
    """
    print(f"Downloading {slice_file.url}")
    try:
        resp = requests.get(slice_file.url, timeout=60)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  Failed to download {slice_file.url}: {exc}")
        return

    # Write the file into a BytesIO buffer.  Bats2d can read from
    # filenames or file‑like objects, but here we save to a temporary file
    # to simplify usage.
    tmp_filename = os.path.join(
        "./", f"{slice_file.plane}_{slice_file.start_time}_{slice_file.end_time}"
    )
    with open(tmp_filename, "wb") as f:
        f.write(resp.content)

    # Load the file with Bats2d.  This reads the header and data arrays.
    try:
        data = Bats2d(tmp_filename)
    except Exception as exc:
        print(f"  Failed to parse {tmp_filename}: {exc}")
        os.remove(tmp_filename)
        return

    # Extract coordinates and pressure.  Bats2d stores variables by
    # dictionary lookup.  The equatorial plane uses x and y coordinates; the
    # meridional plane uses x and z.
    if slice_file.plane == "z0":
        xs = data["x"]
        ys = data["y"]
    else:
        xs = data["x"]
        ys = data["z"]
    ps = data["p"]

    import matplotlib.tri as mtri
    tri = mtri.Triangulation(xs, ys)
    fig, ax = plt.subplots(figsize=(7, 4))
    tcf = ax.tricontourf(tri, ps, levels=64, cmap="RdYlBu_r")
    cbar = fig.colorbar(tcf, ax=ax)
    cbar.set_label("Pressure (nPa)")
    plane_label = "Equatorial" if slice_file.plane == "z0" else "Meridional"
    ax.set_title(
        f"Geospace {plane_label} Cut Plane Pressure\n"
        f"Valid Time: {slice_file.end_time} (run {slice_file.start_time})"
    )
    ax.set_xlabel("X (Re)")
    ax.set_ylabel("Y (Re)" if slice_file.plane == "z0" else "Z (Re)")
    ax.set_aspect("equal")

    # Either show the plot or save it.
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        fig_path = os.path.join(
            save_dir,
            f"{slice_file.plane}_{slice_file.end_time}.png",
        )
        fig.savefig(fig_path, dpi=150)
        print(f"  Saved plot to {fig_path}")
        plt.close(fig)
    else:
        plt.show()

    # Clean up temporary file.
    os.remove(tmp_filename)


def main(start_date_str: str, end_date_str: str, plane: str = "z0", save_dir: str = "./plots") -> None:
    """
    Entry point for batch processing over a date range.

    Parameters
    ----------
    start_date_str : str
        Start date in ISO format (YYYY-MM-DD).
    end_date_str : str
        End date in ISO format (YYYY-MM-DD).
    plane : {'z0', 'y0'}, optional
        Which plane to process.  Defaults to 'z0' (equatorial).
    save_dir : str, optional
        Directory to store plots.  Set to ``None`` to display plots instead
        of saving.
    """
    start_date = _dt.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = _dt.datetime.strptime(end_date_str, "%Y-%m-%d").date()

    for day in daterange(start_date, end_date):
        files = list_slice_files(day, plane=plane)
        if not files:
            print(f"No files found for {day}")
            continue
        for sfile in files:
            download_and_process(sfile, save_dir=save_dir)


if __name__ == "__main__":
    # Example usage.  Adjust the date range and plane as needed.
    # Running this without command-line arguments will process the previous day
    # in the equatorial plane and save plots into './plots'.
    today = _dt.date.today()
    yesterday = today - _dt.timedelta(days=1)
    main(yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d"), plane="z0", save_dir="./plots")