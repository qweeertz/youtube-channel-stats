# YouTube Channel Stats

A small script that uses the YouTube Data API v3 to download metadata for all
videos of a channel (currently `@PietSmiet`), groups them into show formats
based on their titles (e.g. "Quizpoker", "Codenames", "50 Fragen"), and plots
views over time and views vs. duration.

## Setup

1. Create an API key for the **YouTube Data API v3** in the
   [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a virtual environment and install the dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and put your key in it:
   ```
   YT_API_KEY=your_key_here
   ```
   `.env` is git-ignored. Never commit your key.

## Usage

```bash
python yt_channel_stats.py
```

On the first run the script fetches all videos and caches them in
`videos.csv`. Later runs reuse that file (delete it to refetch). It prints a
per-format summary (median views, like rate, comments per 1k views) and writes
two charts:

- `views_over_time.png`
- `views_vs_duration.png`

To analyse another channel, change `handle` in the `__main__` block and adjust
the `FORMATS` patterns to match its video titles.

