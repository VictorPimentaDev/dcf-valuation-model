"""Execute the offline research notebook from any working directory."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
notebook = nbformat.read(root / "notebooks/weg_research.ipynb", as_version=4)
NotebookClient(
    notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(root)}}
).execute()
destination = root / "outputs/weg_research.executed.ipynb"
destination.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(notebook, destination)
print(destination)
