# Separate prototypes — shared design and telemetry

## Prototype 2 update

`prototype_2.html` is the separate updated Prototype 2 file. `index.html` remains Prototype 1 and is not renamed or replaced. Both use the same original shared styling, product settings, five-step checkout, task budget, delivery fields, study inspector, event schema, persistent counters, CSV export, and completion protection. Each has its own browser-storage namespace so their data does not mix when hosted on the same origin.

Prototype 2 retains the original confusion system: a resetting urgency countdown; delivery cost omitted on the product screen and deferred in the cart; a preselected, low-contrast gift-box add-on; and a service charge revealed at payment. The configured default totals remain ৳170 for Prototype 1 and ৳275 for Prototype 2 (৳195 when its gift box is removed). These are simulation settings, not market-price claims. Use the inspector toggle for participant mode without explanatory callouts.

For a separate Netlify site, put a **copy** of `prototype_2.html` into an otherwise empty deployment folder named `index.html` and upload that folder. Do not upload credentials, CSV exports, or the researcher's supporting files. Alternatively, host both current files and open the Prototype 2 filename on the same site.

## Private Google Sheets import — one-shot, not automatic

There was no existing Google Sheets connection in the supplied version. The added `upload_to_sheets.py` imports CSV exports into your private spreadsheet using Google's authenticated Sheets API. It does not run a server, Apps Script web app, background task, or automatic browser collection. A public Apps Script URL is neither needed nor included for this manual workflow. Your 80 friends must export and send you their CSV files; the private Sheet is updated when **you run the importer**. Do not describe this as live centralized tracking.

### One-time setup on the researcher's computer

1. Keep your Google Sheet private. Using the Google account that owns it (or has edit permission), create a blank tab named `Events`. Copy the spreadsheet ID from between `/d/` and `/edit` in its address, not the tab's `gid`.
2. In your own Google Cloud project, enable the **Google Sheets API**. Configure OAuth consent for your organization or for testing with your researcher account as a test user. Create a **Desktop app OAuth client** and download its client JSON to a private local location, outside any Netlify deployment folder.
3. Install Google Cloud CLI separately if needed, then authorize using your own desktop client. No Google password, refresh token, access token, or client JSON belongs in the prototype HTML or repository:

```sh
gcloud auth application-default login --client-id-file=/private/path/oauth-client.json --scopes=https://www.googleapis.com/auth/spreadsheets
```

4. Export CSV from each participant's updated prototype. Save those files locally in an `exports` folder, not the public website. From the workspace, validate them without network access:

```sh
python3 upload_to_sheets.py --dry-run exports/*.csv
```

5. On macOS/Linux, obtain a short-lived access token and run the upload (replace `YOUR_SPREADSHEET_ID` with your actual ID):

```sh
export GOOGLE_ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
python3 upload_to_sheets.py --spreadsheet-id YOUR_SPREADSHEET_ID --tab Events exports/*.csv
unset GOOGLE_ACCESS_TOKEN
```

In PowerShell, set `$env:GOOGLE_ACCESS_TOKEN = gcloud auth application-default print-access-token`, pass explicit CSV paths to the Python command, then `Remove-Item Env:GOOGLE_ACCESS_TOKEN`. Refresh the token if authorization expires. If your organization blocks the consent scope, ask its administrator rather than making the Sheet public.

### Import behavior and checks

The uploader initializes an empty tab's eight-column export header and appends with `RAW` input mode. It rejects incompatible headers and conflicting duplicate event IDs. It checks existing event IDs before appending, so repeated imports do not normally duplicate events; after a timeout it re-reads the Sheet before retrying. **Run only one importer at a time**: Google Sheets does not enforce unique IDs, so concurrent writers are not supported. HTTP authorization errors stop with guidance; temporary network/rate-limit failures use bounded retries. The Sheet must already exist and the `Events` tab must be created first.

Rebuild and run all offline checks:

```sh
python3 split_prototypes.py && node test_prototypes.cjs && python3 test_upload_sheets.py
```

These verify both prototypes and mocked import requests, including a response-lost retry and repeat-import deduplication. No real private Google Sheet has been accessed or verified. After authorization, first import a small test CSV twice and confirm the second import adds no extra rows before collecting real participant data. Event `Group` distinguishes A/B, `click` records clicks, and `complete_order` records completed orders. Prototype dashboards remain local-browser views, not aggregate spreadsheet dashboards.

The API operation used is documented at https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append .

---

# Prototype 1 — telemetry correction

Deploy the regenerated `index.html` on the same Netlify site. It is self-contained; no external assets or build are needed.

## Fixed and tested

- Each page click is logged once, including navigation; four checkout clicks produce four click events. Opening the telemetry tab is itself another click.
- Completed orders are counted from the actual completion event. Duplicate completion attempts do not create extra orders.
- Events, participant identity, active checkout, delivery inputs, and completed orders are saved in browser localStorage and restored after refresh.
- Starting a new session preserves earlier events and orders, and creates a new session ID.
- Telemetry displays persistent click and completion counts and correct average order totals.
- CSV exports include stable event, participant, and session IDs, allowing subsequent deduplication when combining exports.
- The destructive Clear Log control was removed. Storage errors display a warning instead of silently implying data is saved.

## Important: central Google Sheets collection is NOT deployed

This file does not contain a Google Apps Script Web App URL and does not automatically send events to Google Sheets. No authorized Google deployment, Sheet access, or existing ingestion URL was provided. A working URL cannot be fabricated from the supplied files. The dashboard explicitly says it shows this browser only, not all participants.

**Do not distribute this as an automatic 80-participant collection system yet.** A central ingestion endpoint must first be deployed under an authorized Google account and integrated and tested against the actual Sheet. That deployment is not part of this static-file fix. Provide an already-deployed ingestion endpoint and its request format for a subsequent client integration; do not share passwords or private credentials.

Until central collection exists, each participant can export their CSV and send it to the researcher. These exports can be imported into Google Sheets manually. LocalStorage alone cannot collect other people's data or show aggregate results on your device.

## Retention limits

Data is saved only in the same browser profile and site origin. Clearing site data, using private browsing, changing the site address, losing the device, storage eviction, or blocking storage can remove or prevent access to it. Use one active study tab per browser. Export CSV for a separate backup. Browser storage is not a durable database and has a finite quota. Delivery names, phone numbers, and addresses stay in local browser state; event exports contain participant/session IDs and interaction details, not those delivery fields.

Data lost by refreshing the old in-memory version cannot be recovered by this update. New events are retained from this version onward.

## Rebuild and verify

```sh
python3 split_prototypes.py && node test_prototypes.cjs
```

The tests execute the actual embedded script with browser API mocks. They verify click counts, successful completion, refresh persistence, stable identity, duplicate-completion protection, session reset without deleting history, checkout totals, and mode switching. They do not verify a real Google Sheets integration; none is configured.
