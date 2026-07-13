
# CardVault V3 — Dashboard UI

This update redesigns the Streamlit app to match the polished dashboard concept.

## Install

1. Back up your current `adoliscards` folder.
2. Extract this ZIP.
3. Copy the files into your existing GitHub repository folder.
4. Replace matching files.
5. Keep your existing `.streamlit/secrets.toml`.
6. No Supabase migration is required.
7. Run locally:

   ```
   py -m pip install -r requirements.txt
   py -m streamlit run app.py
   ```

8. Commit and push in GitHub Desktop. Streamlit Cloud should redeploy automatically.

## Included

- Dark CardVault sidebar
- Dashboard metric cards
- Progress-by-year panel
- Sets closest to completion
- Recent cards panel
- Collection summary
- Gallery-style collection page
- Mobile Need It shopping mode
- Set progress page
- Analytics page
- Existing Supabase data preserved
