# Ukraine Combat Data Scraper

Automated daily scraper that fetches combat engagement data from Ukrainian General Staff reports.

## What it does

1. Scrapes daily General Staff reports from Ukrinform
2. Extracts combat engagement counts per operational direction (Pokrovsk, Kupiansk, etc.)
3. Saves structured JSON data to `combat-data.json`
4. Runs automatically via GitHub Actions at 8pm Kyiv time daily

## Files

```
├── scraper.py              # Python scraper script
├── combat-data.json        # Output data (auto-updated daily)
├── requirements.txt        # Python dependencies
└── .github/
    └── workflows/
        └── update-combat-data.yml  # GitHub Actions workflow
```

## Setup Instructions

### 1. Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it something like `ukraine-combat-data`
3. Make it **Public** (required for free GitHub Actions and CORS-free access)
4. Click **Create repository**

### 2. Upload the Files

**Option A: Via GitHub Web Interface**
1. Click "uploading an existing file" link on the empty repo page
2. Drag all files from the `ukraine-combat-scraper` folder
3. Make sure the folder structure is preserved (especially `.github/workflows/`)
4. Click "Commit changes"

**Option B: Via Git Command Line**
```bash
cd ukraine-combat-scraper
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ukraine-combat-data.git
git push -u origin main
```

### 3. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. If prompted, click "I understand my workflows, go ahead and enable them"
4. The workflow will now run automatically every day at 6pm UTC (8pm Kyiv time)

### 4. Test the Workflow

1. Go to **Actions** tab
2. Click "Update Combat Data" workflow
3. Click **Run workflow** → **Run workflow** button
4. Wait ~30 seconds for it to complete
5. Check that `combat-data.json` was updated

### 5. Get Your Data URL

Your combat data will be available at:

```
https://raw.githubusercontent.com/YOUR_USERNAME/ukraine-combat-data/main/combat-data.json
```

Replace `YOUR_USERNAME` with your GitHub username.

## Using in Your Map

Add this URL to your map's JavaScript to fetch live data:

```javascript
const COMBAT_DATA_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/ukraine-combat-data/main/combat-data.json';

async function fetchCombatData() {
    try {
        const response = await fetch(COMBAT_DATA_URL);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Failed to fetch combat data:', error);
        return null;
    }
}
```

## Data Format

```json
{
  "date": "2025-11-25",
  "source": "Ukrainian General Staff",
  "totalEngagements": 107,
  "lastUpdate": "2025-11-25T18:00:00Z",
  "frontSectors": [
    {
      "name": "pokrovsk",
      "displayName": "Pokrovsk",
      "coords": [48.28, 37.18],
      "combatEngagements": 35,
      "heat": "extreme",
      "polygon": [[48.45, 36.90], ...]
    },
    ...
  ],
  "casualties": {
    "russia": { "total": 1167570, "daily": 1120 },
    "ukraine": { "total": 400000, "daily": null }
  }
}
```

## Heat Levels

| Engagements | Heat Level |
|-------------|------------|
| 30+         | extreme    |
| 15-29       | high       |
| 8-14        | medium     |
| 3-7         | low        |
| 0-2         | quiet      |

## Troubleshooting

**Workflow not running?**
- Check Actions tab is enabled
- Make sure the `.github/workflows/` folder exists with the YAML file

**Data not updating?**
- Check the workflow logs in Actions tab for errors
- The scraper falls back to cached data if Ukrinform is unavailable

**CORS errors in browser?**
- Make sure your repo is **Public**
- Use the `raw.githubusercontent.com` URL, not the regular GitHub URL

## Manual Update

To update data manually:
1. Go to Actions tab
2. Click "Update Combat Data"  
3. Click "Run workflow" → "Run workflow"

## License

Data source: Ukrainian General Staff via Ukrinform
