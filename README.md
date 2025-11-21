# Alberta Pathfinding Tool (Prototype)

Open-source Streamlit app for searching small business programs, funding and supports in Alberta.

## Repository notes
- The root-level `.gitignore` sits beside `app.py` and `requirements.txt`. In GitHub's file list it may be hidden by default; click the **Toggle hidden files** (eyeball) icon to reveal it and add new ignore rules there.

### Applying GitHub patches locally
- When GitHub shows "Copy git apply" vs. "Copy git patch" on a file diff, choose **Copy git apply** if you plan to paste into `git apply` for a quick local patch. Use **Copy git patch** only when piping into `git am` (which preserves commit metadata). For single-file tweaks like `app.py`, copy the **git apply** snippet, save it to a file (e.g., `change.patch`), and run `git apply change.patch` from the repo root.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
