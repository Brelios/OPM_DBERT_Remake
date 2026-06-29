import sys
import os
import math
import glob
import re
from contextlib import asynccontextmanager
from collections import Counter, defaultdict

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root to path so we can import from predictions.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from predictions import SentimentAnalyzer

# ── Global State ──────────────────────────────────────────────────────────────
df: pd.DataFrame = None
analyzer: SentimentAnalyzer = None

LABEL_MAP = {
    0: "Very Negative",
    1: "Negative",
    2: "Neutral",
    3: "Positive",
    4: "Very Positive",
}

# ── Startup / Lifespan ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global df, analyzer

    print("Loading dataset...")
    files = glob.glob("Dataset-SA.csv")
    if not files:
        files = glob.glob("../Dataset-SA.csv")
    if not files:
        raise RuntimeError("Dataset-SA.csv not found. Please place it in the project root.")
    df = pd.read_csv(files[0], usecols=["product_name", "Rate", "Review", "Sentiment"])
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["Review"] = df["Review"].astype(str).str.strip()
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
    df.dropna(subset=["product_name", "Review"], inplace=True)
    df = df[df["product_name"] != ""]
    df = df[df["Review"] != ""]
    print(f"Dataset loaded: {len(df):,} rows")

    print("Loading sentiment model...")
    model_dir = "saved_model" if os.path.exists("saved_model") else "../saved_model"
    analyzer = SentimentAnalyzer(model_dir=model_dir)
    print("Sentiment model ready!")

    yield

app = FastAPI(title="OpinionMeter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def calculate_verdict(sentiment_counts: dict, total: int) -> dict:
    if total == 0:
        return {"label": "UNKNOWN", "color": "gray", "description": "Not enough data."}
    
    very_pos = sentiment_counts.get("Very Positive", 0)
    pos = sentiment_counts.get("Positive", 0)
    very_neg = sentiment_counts.get("Very Negative", 0)
    neg = sentiment_counts.get("Negative", 0)
    neutral = sentiment_counts.get("Neutral", 0)

    positive_pct = (very_pos + pos) / total
    negative_pct = (very_neg + neg) / total

    if positive_pct >= 0.75:
        return {"label": "HIGHLY RECOMMENDED", "color": "emerald",
                "description": f"{positive_pct:.0%} of reviewers loved this product. A clear winner."}
    elif positive_pct >= 0.55:
        return {"label": "RECOMMENDED", "color": "green",
                "description": f"Most customers ({positive_pct:.0%}) are happy with this purchase."}
    elif negative_pct >= 0.55:
        return {"label": "AVOID", "color": "red",
                "description": f"{negative_pct:.0%} of reviewers had a negative experience. Proceed with caution."}
    else:
        return {"label": "MIXED REVIEWS", "color": "amber",
                "description": "Customers have widely varying opinions. Read the reviews carefully before buying."}


def get_representative_reviews(reviews_df: pd.DataFrame, predictions: list, n: int = 2) -> dict:
    """Pick the top n highest-confidence reviews per sentiment class."""
    by_class = defaultdict(list)
    for pred, (_, row) in zip(predictions, reviews_df.iterrows()):
        by_class[pred["label"]].append({
            "text": row["Review"][:300],
            "label": pred["label"],
            "confidence": pred["confidence"]
        })
    
    result = {}
    for label, items in by_class.items():
        items_sorted = sorted(items, key=lambda x: x["confidence"], reverse=True)
        result[label] = items_sorted[:n]
    return result


def find_competitors(product_name: str, limit: int = 5) -> list:
    """Find products that share keywords with the given product name."""
    # Extract meaningful words (skip short/common words)
    stopwords = {"with", "and", "for", "the", "in", "of", "a", "an", "l", "w", "kg",
                  "cm", "mm", "gb", "mb", "inch", "g", "ml"}
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', product_name.lower())) - stopwords
    
    if not words:
        return []
    
    # Count word overlaps for each unique product
    unique_products = df["product_name"].dropna().unique()
    scores = []
    clean_name = product_name.lower()
    
    for pname in unique_products:
        if pname.lower() == clean_name:
            continue
        pwords = set(re.findall(r'\b[a-zA-Z]{3,}\b', pname.lower())) - stopwords
        overlap = len(words & pwords)
        if overlap >= 1:
            scores.append((pname, overlap))

    scores.sort(key=lambda x: x[1], reverse=True)
    top = [s[0] for s in scores[:limit]]
    
    # Enrich with review count and avg rating
    result = []
    for pname in top:
        sub = df[df["product_name"] == pname]
        avg_rate = sub["Rate"].mean()
        result.append({
            "name": pname,
            "review_count": len(sub),
            "avg_rating": round(avg_rate, 1) if not math.isnan(avg_rate) else None,
        })
    return result

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/suggest")
def suggest(q: str = Query(..., min_length=1), limit: int = 10):
    """Autocomplete product names based on a prefix/substring."""
    q_lower = q.lower()
    unique_names = df["product_name"].dropna().unique()

    starts_with = [n for n in unique_names if n.lower().startswith(q_lower)]
    contains = [n for n in unique_names if q_lower in n.lower() and not n.lower().startswith(q_lower)]

    combined = (starts_with + contains)[:limit]
    return {"suggestions": combined[:limit]}


@app.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = 24):
    """Search for products matching a keyword. Returns product cards."""
    q_lower = q.lower()
    
    mask = df["product_name"].str.lower().str.contains(q_lower, regex=False, na=False)
    matched = df[mask]

    if matched.empty:
        return {"query": q, "count": 0, "products": []}

    # Group by product name
    grouped = matched.groupby("product_name")
    products = []
    for name, group in grouped:
        avg_rate = group["Rate"].mean()
        rate_counts = group["Rate"].value_counts().sort_index()
        
        # Dominant sentiment from pre-labeled data (fast, no ML inference)
        if "Sentiment" in group.columns:
            dominant = group["Sentiment"].mode().iloc[0] if not group["Sentiment"].mode().empty else "unknown"
        else:
            dominant = "unknown"

        products.append({
            "name": name,
            "review_count": len(group),
            "avg_rating": round(avg_rate, 1) if not math.isnan(avg_rate) else None,
            "dominant_sentiment": dominant,
        })

    # Sort by review count descending
    products.sort(key=lambda x: x["review_count"], reverse=True)
    return {"query": q, "count": len(products), "products": products[:limit]}


@app.get("/product")
def product_detail(name: str = Query(...), limit: int = 60):
    """Full product analysis: sentiment breakdown, rating distribution, verdict, competitors."""
    mask = df["product_name"].str.lower() == name.lower()
    subset = df[mask].head(limit)

    if subset.empty:
        raise HTTPException(status_code=404, detail="Product not found.")

    reviews = subset["Review"].tolist()

    # Run BERT sentiment predictions
    predictions = [analyzer.predict(r) for r in reviews]

    # Sentiment breakdown
    label_counts = Counter(p["label"] for p in predictions)
    total = len(predictions)
    avg_confidence = sum(p["confidence"] for p in predictions) / total if total else 0

    sentiment_data = [
        {"label": LABEL_MAP[i], "count": label_counts.get(LABEL_MAP[i], 0),
         "percentage": round(label_counts.get(LABEL_MAP[i], 0) / total * 100, 1) if total else 0}
        for i in range(5)
    ]

    # Rating distribution
    rating_dist = []
    for star in [1, 2, 3, 4, 5]:
        count = int(subset[subset["Rate"] == star].shape[0])
        rating_dist.append({"stars": star, "count": count})

    avg_rating = subset["Rate"].mean()

    # Representative reviews per class
    representative = get_representative_reviews(subset, predictions)

    # Verdict
    verdict = calculate_verdict(dict(label_counts), total)

    # Competitors
    competitors = find_competitors(name)

    return {
        "name": name,
        "review_count": total,
        "avg_rating": round(avg_rating, 1) if not math.isnan(avg_rating) else None,
        "avg_confidence": round(avg_confidence, 4),
        "sentiment_breakdown": sentiment_data,
        "rating_distribution": rating_dist,
        "verdict": verdict,
        "representative_reviews": representative,
        "competitors": competitors,
    }


@app.get("/summary")
def product_summary(name: str = Query(...), limit: int = 30):
    """Generate Qwen-powered summary + pros/cons. Called async by frontend."""
    mask = df["product_name"].str.lower() == name.lower()
    subset = df[mask].head(limit)

    if subset.empty:
        raise HTTPException(status_code=404, detail="Product not found.")

    reviews = subset["Review"].tolist()
    summary_text = analyzer.summarize_reviews(reviews)

    # Parse Pros/Cons sections from Qwen output
    pros, cons, summary_para = [], [], ""
    lines = summary_text.split("\n")
    mode = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("summary"):
            mode = "summary"
            continue
        elif line.lower().startswith("pro"):
            mode = "pros"
            continue
        elif line.lower().startswith("con"):
            mode = "cons"
            continue

        if mode == "summary":
            summary_para += line + " "
        elif mode == "pros":
            clean = re.sub(r"^[\d\.\-\*]+\s*", "", line)
            if clean:
                pros.append(clean)
        elif mode == "cons":
            clean = re.sub(r"^[\d\.\-\*]+\s*", "", line)
            if clean:
                cons.append(clean)

    return {
        "name": name,
        "summary": summary_para.strip() or summary_text,
        "pros": pros,
        "cons": cons,
        "raw": summary_text,
    }
