import os
import subprocess
import sys

from .config import PATHS


def launch_tab(tab_name, *args, wait=False):
    """Launch a helper script associated with a tab name.

    Parameters
    ----------
    tab_name : str
        Name of the tab / PATHS attribute (e.g. "business").
    *args : str
        Additional arguments passed to the script.
    wait : bool, optional
        If True run the command synchronously.
    """
    script_path = getattr(PATHS, tab_name, None)
    if script_path is None:
        raise ValueError(f"Unknown tab '{tab_name}'")

    module = f"app.{os.path.splitext(os.path.basename(script_path))[0]}"
    cmd = [sys.executable, "-m", module, *args]

    if wait:
        subprocess.run(cmd)
    else:
        subprocess.Popen(cmd)