# Alberta Pathfinding Tool (Prototype)

Open-source Streamlit app for searching small business programs, funding and supports in Alberta.

## Repository notes
- The root-level `.gitignore` sits beside `app.py` and `requirements.txt`. In GitHub's file list it may be hidden by default; click the **Toggle hidden files** (eyeball) icon to reveal it and add new ignore rules there.

## Project structure
- `app.py` – Streamlit entry point for the Alberta Pathfinding Tool. Run it from the repository root so relative paths resolve correctly.
- `Pathfinding_Master.xlsx` – default data source loaded by `app.py` from the root directory.
- `assets/` – static files such as `GoA-logo.svg` and `GoA-logo.png` that the app loads if present.
- `docs/` – documentation assets (for example screenshots or supporting notes).
- `requirements.txt` – Python dependencies for running the Streamlit app.

### Applying GitHub patches locally
- When GitHub shows "Copy git apply" vs. "Copy git patch" on a file diff, choose **Copy git apply** if you plan to paste into `git apply` for a quick local patch. Use **Copy git patch** only when piping into `git am` (which preserves commit metadata). For single-file tweaks like `app.py`, copy the **git apply** snippet, save it to a file (e.g., `change.patch`), and run `git apply change.patch` from the repo root.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
