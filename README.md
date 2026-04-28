# Trade Journal App

This is a local trade journal web app for recording trades, storing chart screenshots, reviewing full trade details, and exporting the journal to Excel or CSV.

## What This App Does

The app gives you:

- A trade entry form
- Automatic trade saving
- Local screenshot upload and storage
- A dashboard with saved trades
- A detailed trade review panel
- Export to `.csv` and `.xlsx`

Each saved trade can include:

- Trade date
- Instrument
- Account
- Long or Short
- Setup type
- Timeframe
- Entry price
- Stop loss
- Take profit
- Contracts
- Result
- Win / Loss / Breakeven
- RR ratio
- Emotion
- Mistake category
- Screenshot image
- Notes

## How It Works

This project is a small local app with:

- `server.py` for the backend
- `public/` for the frontend
- `data/trades.json` for saved trade records
- `uploads/` for uploaded images

When you save a trade:

1. The form sends the trade details to the backend.
2. The backend stores the trade in `data/trades.json`.
3. If an image is uploaded, it is saved in `uploads/`.
4. The dashboard refreshes and shows the trade in the journal list.
5. Clicking the trade opens the full detail view with the screenshot and all notes.

## Main Files

- [server.py](C:/Users/Vrajkumar/Documents/Codex/2026-04-28/i-want-to-create-automatic-trade/server.py)
- [start-trade-journal.bat](C:/Users/Vrajkumar/Documents/Codex/2026-04-28/i-want-to-create-automatic-trade/start-trade-journal.bat)
- [public/index.html](C:/Users/Vrajkumar/Documents/Codex/2026-04-28/i-want-to-create-automatic-trade/public/index.html)
- [public/app.js](C:/Users/Vrajkumar/Documents/Codex/2026-04-28/i-want-to-create-automatic-trade/public/app.js)
- [public/styles.css](C:/Users/Vrajkumar/Documents/Codex/2026-04-28/i-want-to-create-automatic-trade/public/styles.css)

## How To Start The App

Double-click:

```bat
start-trade-journal.bat
```

By default it starts on:

```text
http://127.0.0.1:3000
```

You can also run it with a custom port:

```bat
start-trade-journal.bat 3001
```

## Storage Location

The app is now portable.

It uses a storage root called `TRADE_JOURNAL_HOME`.

If you do not set anything manually, the app stores data and images in the same folder where the app is located.

That means if you copy the whole app folder to `M:`, it will automatically save there.

Example:

```text
M:\TradeJournal\
```

If you run the app from that folder, it will store files here:

```text
M:\TradeJournal\data\trades.json
M:\TradeJournal\uploads\
```

## Run From M Drive

### Option 1: Copy The Whole Folder To M Drive

Copy the full app folder to `M:` and run:

```bat
start-trade-journal.bat
```

Because the launcher uses its own folder as the default storage root, the app will save all journal data and screenshots on `M:`.

### Option 2: Use A Separate Storage Folder On M Drive

You can also keep the app anywhere and force storage to a folder on `M:`.

Example:

```bat
start-trade-journal.bat 3000 "M:\TradeJournal"
```

This stores data in:

```text
M:\TradeJournal\data\
M:\TradeJournal\uploads\
```

## Moving Existing Data

If you already have trades and screenshots, copy these folders to the new location:

- `data`
- `uploads`

This keeps:

- old trade records
- uploaded screenshots
- export-ready journal history

## Export

The app supports:

- CSV export
- Excel export

Use the buttons in the top-right of the app:

- `Export CSV`
- `Export Excel`

Exports include trade details and screenshot file/path information.

## Dashboard

The dashboard includes:

- Search
- Trade list
- Trade stats
- Win rate
- Full detail panel
- Large screenshot preview

Clicking a trade opens:

- full trade information
- screenshot image
- notes
- review details

## Image Uploads

Screenshot images are uploaded directly from your computer.

Supported image types:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.gif`

Images are stored locally inside the `uploads` folder.

When a trade is deleted, its uploaded image is deleted too.

## Notes

- This app is local and single-user.
- It does not require an external database.
- Trade records are stored in JSON.
- Images are stored as files on disk.

## Quick Start Summary

1. Copy the app folder where you want it, including `M:`.
2. Keep `data` and `uploads` if you want existing history.
3. Run `start-trade-journal.bat`.
4. Open `http://127.0.0.1:3000`.
5. Add trades, upload images, review details, and export when needed.
