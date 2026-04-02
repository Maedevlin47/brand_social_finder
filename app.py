"""
Flask web UI for brand_handle_finder.

Run with:
    python app.py
Then open http://localhost:5000 in your browser.
"""

import csv
import io
import json
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from searcher import BrandSearcher

load_dotenv()

app = Flask(__name__)


def _get_searcher() -> BrandSearcher:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    return BrandSearcher(api_key=key)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json(force=True)
    brand_name = (data.get("brand_name") or "").strip()
    source_name = (data.get("source_name") or "").strip()
    country = (data.get("country") or "").strip()

    if not brand_name or not country:
        return jsonify({"error": "Brand name and country are required"}), 400

    try:
        searcher = _get_searcher()
        result = searcher.search(brand_name=brand_name, source_name=source_name, country=country)
        return jsonify({"brand_name": brand_name, "source_name": source_name, "country": country, **result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/batch", methods=["POST"])
def batch():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        brands = [
            {
                "brand_name": row["Name"].strip(),
                "source_name": row.get("List", "").strip(),
                "country": row["Location"].strip(),
            }
            for row in reader
            if row.get("Name", "").strip()
        ]
    except Exception as exc:
        return jsonify({"error": f"Invalid CSV: {exc}"}), 400

    if not brands:
        return jsonify({"error": "CSV is empty or missing required columns"}), 400

    def generate():
        try:
            searcher = _get_searcher()
        except ValueError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return

        for brand in brands:
            try:
                result = searcher.search(**brand)
                row = {**brand, **result}
            except Exception as exc:
                row = {
                    **brand,
                    "instagram_handle": "",
                    "twitter_handle": "",
                    "notes": f"Error: {exc}",
                }
            yield f"data: {json.dumps(row)}\n\n"

        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
