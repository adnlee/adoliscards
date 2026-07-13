
# Adolis García Rangers-Era Cloud Database

This version is designed to stay online and sync between your phone and computer.

## What it includes

- Supabase email/password login
- Private per-user collection data
- Row Level Security
- Synced cards, status, prices, notes, and storage locations
- Private card-photo storage
- Signed image URLs
- Mobile Need It mode
- Dashboard and CSV backup
- Streamlit Community Cloud deployment configuration

## Part 1 — Create Supabase

1. Create a free Supabase account and project.
2. In your project, open **SQL Editor**.
3. Paste and run the full contents of `supabase_setup.sql`.
4. Open **Project Settings → API**.
5. Copy:
   - Project URL
   - Publishable/anon key
6. Under **Authentication → Providers → Email**, leave email/password enabled.
7. For easiest initial setup, you may temporarily disable email confirmation. Keeping confirmation enabled is more secure.

Never place the Supabase service-role key in this app. Use only the anon/publishable key.

## Part 2 — Test locally

1. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.
2. Replace the placeholders with your Supabase URL and anon key.
3. Install Python 3.11+.
4. Run:

   Windows:
   ```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

   Mac:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Part 3 — Put it on GitHub

1. Create a new private GitHub repository.
2. Upload the files from this folder.
3. Do not upload `.streamlit/secrets.toml`.
4. The included `.gitignore` already excludes it.

## Part 4 — Deploy with Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud using GitHub.
2. Select your repository.
3. Set the entrypoint to `app.py`.
4. Open **Advanced settings / Secrets** and paste:

   ```
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your-anon-key"
   ```

5. Deploy.
6. Choose a memorable `streamlit.app` subdomain.

## Part 5 — Add it to your iPhone Home Screen

1. Open the deployed URL in Safari.
2. Tap Share.
3. Tap **Add to Home Screen**.
4. Launch it from the new icon.

## Security notes

- Each card row includes the authenticated user's ID.
- Supabase Row Level Security only permits users to access their own rows.
- Card photos are stored in a private bucket under each user's ID folder.
- Images are displayed through temporary signed URLs.
- The service-role key is not required and must not be used in Streamlit secrets.

## Importing the larger checklist

1. Deploy or run this updated version of `app.py`.
2. Sign in and open **Import**.
3. Upload the checklist CSV.
4. Review the preview and duplicate count.
5. Optionally select **Delete the original 27 starter rows** only when you have not edited those rows.
6. Confirm and click **Import checklist**.

The importer recognizes common columns including `year`, `set_name`/`set`, `card_number`, `card_name`, `category`, `variation`, `serial_numbered_to`, `owned`, `source_url`, and `verification_status`. Exact duplicates are skipped using year, set, card number, card name, and parallel.
