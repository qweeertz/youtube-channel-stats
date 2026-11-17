import re
import os
from dotenv import load_dotenv
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

API = "https://www.googleapis.com/youtube/v3"
load_dotenv()
KEY = os.environ["YT_API_KEY"]


# Funktionen für die YouTube Data API (v3)


def get(endpoint, **params):
    r = requests.get(f"{API}/{endpoint}", params={**params, "key": KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


def uploads_playlist_id(handle):
    """Jeder Kanal hat eine Playlist mit allen Uploads."""
    data = get("channels", part="contentDetails,snippet", forHandle=handle)
    item = data["items"][0]
    print("Kanal:", item["snippet"]["title"])
    return item["contentDetails"]["relatedPlaylists"]["uploads"]


def all_video_ids(playlist_id, max_videos=None):
    ids, token = [], None
    while True:
        data = get(
            "playlistItems",
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,  # playlistItems.list nimmt max. 50 Ergebnisse pro Seite
            pageToken=token,
        )
        ids += [i["contentDetails"]["videoId"] for i in data["items"]]
        token = data.get("nextPageToken")
        if not token or (max_videos and len(ids) >= max_videos):
            break
    return ids[:max_videos] if max_videos else ids


def video_details(ids):
    rows = []
    for i in range(0, len(ids), 50):  # videos.list nimmt max. 50 IDs
        data = get(
            "videos",
            part="snippet,statistics,contentDetails",
            id=",".join(ids[i : i + 50]),
        )
        for v in data["items"]:
            s, st = v["snippet"], v.get("statistics", {})
            rows.append(
                {
                    "id": v["id"],
                    "title": s["title"],
                    "published": s["publishedAt"],
                    "duration": v["contentDetails"]["duration"],
                    "views": int(st.get("viewCount", 0)),
                    "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)),
                }
            )
    df = pd.DataFrame(rows)
    df["published"] = pd.to_datetime(df["published"])
    df["duration_min"] = pd.to_timedelta(df["duration"]).dt.total_seconds() / 60
    df["like_rate"] = df["likes"] / df["views"]
    df["comments_per_1k_views"] = df["comments"] / df["views"] * 1000
    return df


# Klassifizierung der Formate anhand der Titel der Videos


FORMATS = {
    "50 Fragen": re.compile(r"\b50\b.*?\bfragen\b", re.IGNORECASE),
    "Quizpoker": re.compile(r"quizpoker", re.IGNORECASE),
    "Guess the Game": re.compile(r"guess the game", re.IGNORECASE),
    "Jahresbattle": re.compile(r"jahresbattle", re.IGNORECASE),
    "Spot It": re.compile(r"spot it", re.IGNORECASE),
    "Einen Hinweis, bitte": re.compile(r"\beinen hinweis\b.*?\bbitte\b", re.IGNORECASE),
    "Schnittchenduell": re.compile(r"schnittchenduell", re.IGNORECASE),
    "Brain Battle": re.compile(r"brain battle", re.IGNORECASE),
    "Die Ordnungshüter": re.compile(r"ordnungshüter", re.IGNORECASE),
    "Codenames": re.compile(r"codenames", re.IGNORECASE),
}


def tag_format(title):
    for name, pattern in FORMATS.items():
        if pattern.search(title):
            return name
    return "Andere"


# Funktionen für das Plotten der Statistiken


def scatterplot_quiz_formats(
    df, x, y, xlabel, ylabel, filename, xformat="number", yscale="linear"
):

    fig, ax = plt.subplots(figsize=(10, 5))
    for name, g in df.groupby("format"):
        if name != "Andere":
            ax.scatter(g[x], g[y], label=name, s=10)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_yscale(yscale)
    if xformat == "date":
        locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.legend()
    fig.tight_layout()
    fig.savefig(filename, dpi=150)


if __name__ == "__main__":
    handle = "@PietSmiet"
    if not os.path.exists("videos.csv"):
        ids = all_video_ids(uploads_playlist_id(handle), max_videos=None)
        df = video_details(ids)
        df["format"] = df["title"].map(tag_format)
        df.to_csv("videos.csv", index=False)
    else:
        df = pd.read_csv("videos.csv", parse_dates=["published"])
        df["format"] = df["title"].map(tag_format)

    summary = (
        df.groupby("format")
        .agg(
            videos=("id", "count"),
            median_views=("views", "median"),
            median_like_rate=("like_rate", "median"),
            median_comments_per_1k=("comments_per_1k_views", "median"),
        )
        .sort_values("median_views", ascending=False)
    )
    print(summary)

    # Aufrufe pro Video über die Zeit, nach Format eingefärbt
    scatterplot_quiz_formats(
        df,
        "published",
        "views",
        "Veröffentlichungsdatum",
        "Aufrufe",
        "views_over_time.png",
        xformat="date",
        yscale="linear",
    )

    # Aufrufe pro Video vs. Dauer, nach Format eingefärbt
    scatterplot_quiz_formats(
        df,
        "duration_min",
        "views",
        "Dauer (Minuten)",
        "Aufrufe",
        "views_vs_duration.png",
        yscale="linear",
    )
