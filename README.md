# Indian Stock Screener Agent

Fetches NSE stock price data + news, scores each stock on a transparent
technical + sentiment model, and outputs a shortlist with entry zone,
target price, and stop-loss. Runs daily and weekly, fully on free tools.

**This is decision-support, not financial advice.** All scores/targets are
rule-based heuristics on public data — verify independently before trading.

## Stack (all free)
| Piece | Tool |
|---|---|
| Price/volume data | `yfinance` (Yahoo Finance, free, no key) |
| News | Google News RSS (free, no key) |
| Technicals | `ta` python library (RSI, SMA) |
| Sentiment | Rule-based keyword scoring (free) — optional LLM upgrade via Groq's free tier |
| Scheduling | GitHub Actions (free 2,000 min/month) |
| API for your frontend | FastAPI, deployable free on Render/Railway/Fly.io |

## 1. Run it locally first
```bash
pip install -r requirements.txt
python screener.py daily
python screener.py weekly
```
This writes `output/daily_screen.json` and `output/weekly_screen.json`.

## 2. Serve it to a frontend
```bash
uvicorn api:app --reload --port 8000
```
Your frontend calls:
- `GET /recommendations/daily`
- `GET /recommendations/weekly`
- `POST /run/daily` — triggers a fresh screen on demand

## 3. Automate it (free, no server needed)
Push this repo to GitHub. The included workflow
`.github/workflows/scheduled-screen.yml` runs automatically:
- Weekdays 9:00 AM IST → daily screen
- Sundays 7:30 AM IST → weekly screen

Results get committed back to `output/` in the repo automatically — free forever
via GitHub Actions, no server required. Your frontend can fetch the JSON
straight from the raw GitHub URL, or you host the FastAPI app separately
(step 4) if you want a live-trigger endpoint too.

## 4. Full setup: button-triggered + cron + permanent history (recommended)

This is the architecture that answers "store daily/previous data, let anyone
view without hitting an API, but still let me press a button to force a run":

```
GitHub repo (source of truth)
 ├─ .github/workflows/scheduled-screen.yml   → cron runs screener.py, commits JSON
 ├─ output/daily/2026-08-12.json             → permanent dated snapshot (history!)
 ├─ output/daily/latest.json                 → always the newest run
 ├─ output/weekly/...                        → same pattern
 ├─ output/index.json                        → list of every available date
 └─ frontend/index.html                      → static page, reads JSON directly from GitHub

Vercel (free)
 ├─ serves frontend/index.html               → the page anyone opens
 └─ api/trigger.js (serverless function)     → what the "Run Now" button calls
```

**Why it works this way:** the frontend page never calls a live API to display
data — it fetches the already-committed JSON straight from GitHub's raw file
URLs, which is instant and free. The "Run Now" button is the only thing that
triggers actual computation, via a tiny serverless function that kicks off
the same GitHub Actions workflow your cron uses. Every run — scheduled or
button-triggered — gets committed to `output/{mode}/{date}.json` and stays
in git forever, so target prices from any past day are always checkable.

### Step-by-step

**1. Push this project to GitHub**
```bash
cd stock-agent
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/stock-agent.git
git push -u origin main
```
Keep the repo public — `output/` needs to be readable via raw GitHub URLs
without auth for the frontend to load it for free.

**2. Let the cron run once to confirm it works**
In GitHub → your repo → Actions tab → "Stock Screener - Scheduled Run" →
"Run workflow" (manual trigger). Check that `output/daily/latest.json` and
`output/index.json` appear in the repo after ~1 minute.

**3. Point the frontend at your repo**
Edit `frontend/index.html`, top of the `<script>` block:
```js
const GITHUB_USER = "your-actual-username";
const GITHUB_REPO = "stock-agent";
```

**4. Create a GitHub token for the button**
GitHub → Settings → Developer settings → Fine-grained tokens → Generate new.
Scope it to just this repo, permission "Actions: Read and write". Copy the token.

**5. Deploy to Vercel**
```bash
npm install -g vercel
cd stock-agent
vercel
```
Follow the prompts (link/create project). This deploys both the static
frontend and the `api/trigger.js` function together.

**6. Add the token as an environment variable in Vercel**
Vercel dashboard → your project → Settings → Environment Variables, add:
- `GITHUB_TOKEN` = the token from step 4
- `GITHUB_OWNER` = your GitHub username
- `GITHUB_REPO` = `stock-agent`

Redeploy (`vercel --prod`) so the function picks up the new env vars.

**7. Open your Vercel URL**
Anyone who opens it sees the latest stored snapshot instantly (no API call,
no waiting). The date dropdown lets them browse any past day. Pressing
"Run Now" fires a fresh GitHub Actions run in the background — refresh after
~1-2 minutes to see it appear, both on the page and as a new dated file in
`output/` permanently.

### Alternative: skip Vercel entirely
If you don't need the on-demand button, you can skip steps 4-6 entirely —
enable GitHub Pages on the repo (Settings → Pages → deploy from `frontend/`
folder) and you get free permanent hosting for the viewing page with zero
serverless setup. You'd lose the "Run Now" button, but the cron keeps
everything updated automatically and history stays forever either way.

## 5. (Optional) Smarter written reasoning
By default, each shortlisted stock gets a rule-based explanation — free,
no API key. If you want an LLM to write a sharper 3-sentence rationale:
1. Get a free key at console.groq.com (fast, generous free tier)
2. `export GROQ_API_KEY=your_key`
3. In `screener.py`, call `run_screen(mode, use_llm_reasoning=True)`

## Expanding the stock universe
`config.py` ships with Nifty 50 tickers. Add any NSE ticker with `.NS`
suffix (e.g. `"ZOMATO.NS"`) to `NIFTY50` list to widen coverage — Nifty 500
list is easy to paste in from any public NSE index constituents page.

## How scoring works (transparent, not a black box)
See `technical_analysis.py::score_setup()` — starts at 50, then adjusts for:
RSI zone, price vs 20/50-day moving averages, volume confirmation, and
5-day momentum. News sentiment (`sentiment.py`) then nudges the score
±8 to ±15 based on keyword-matched recent headlines.

## Important limits to know
- Free Yahoo Finance data can lag or occasionally be unavailable — the
  agent retries but isn't a professional market-data feed.
- Google News RSS surfaces headlines, not full sentiment-verified analysis.
- Nothing here predicts the future. Treat scores as a starting shortlist
  for your own research, not a signal to act on blindly.
