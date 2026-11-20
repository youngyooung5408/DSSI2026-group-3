"""Read each image-based 2026 platform box with Tesseract chi_tra (PSM 3).
Set TESSDATA_PREFIX to a directory containing tessdata_fast/chi_tra.traineddata.
Source: https://github.com/tesseract-ocr/tessdata_fast/blob/main/chi_tra.traineddata
"""

import csv
import hashlib
import json
import subprocess
import tempfile
import io
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from bulletin_2026_helpers import MANUAL_CARDS, detect_cards, regions


def extract(root):
    weights = Path(os.environ["TESSDATA_PREFIX"]) / "chi_tra.traineddata"
    assert (
        hashlib.sha256(weights.read_bytes()).hexdigest()
        == "529c5b5797d64b126065cd55f2bb4c7fd7b15790798091b1ff259941a829330b"
    )
    corpus = root / "data/processed/candidate_bulletin_2026.csv"
    manifest = json.loads(
        (root / "data/raw/cec_bulletin_2026/file_manifest.json").read_text()
    )
    hashes = {m["path"]: m["sha256"] for m in manifest}
    with corpus.open(encoding="utf-8-sig") as stream:
        rows = [r for r in csv.DictReader(stream) if r["platform_source"] == "ocr"]
    results = {}
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        jobs = []
        for filename in dict.fromkeys(r["file"] for r in rows):
            pdf_path = root / filename
            assert hashlib.sha256(pdf_path.read_bytes()).hexdigest() == hashes[filename]
            relative = filename.split("cec_bulletin_2026/")[1]
            selected = [r for r in rows if r["file"] == filename]
            with pdfium.PdfDocument(pdf_path) as document:
                for number in sorted({int(float(r["page"])) for r in selected}):
                    page = document[number - 1]
                    found = MANUAL_CARDS.get((relative, number)) or detect_cards(
                        np.asarray(page.render(scale=1).to_pil().convert("L"))
                    )
                    for r in [r for r in selected if int(float(r["page"])) == number]:
                        expected = json.loads(r["card_bbox"])

                        def distance(c):
                            return sum(
                                abs(a - b)
                                for a, b in zip(
                                    expected,
                                    (c["x0"], c["top"], c["x1"], c["bottom"]),
                                )
                            )

                        c = min(found, key=distance)
                        assert distance(c) <= 12, (r["card_id"], expected)
                        box = regions(c)["platform"]
                        x0, top, x1, bottom = box
                        w, h = page.get_size()
                        image = page.render(
                            scale=5, crop=(x0, h - bottom, w - x1, top)
                        ).to_pil()
                        path = temp / (r["card_id"] + ".png")
                        image.save(path)
                        jobs.append((box, path))

        def recognize(item):
            box, path = item
            response = subprocess.run(
                [
                    "tesseract",
                    str(path),
                    "stdout",
                    "-l",
                    "chi_tra",
                    "--psm",
                    "3",
                    "-c",
                    "tessedit_create_tsv=1",
                ],
                env={**os.environ, "OMP_THREAD_LIMIT": "1"},
                capture_output=True,
                check=True,
            )
            tokens = list(
                csv.DictReader(
                    io.StringIO(response.stdout.decode()),
                    delimiter="\t",
                    quoting=csv.QUOTE_NONE,
                )
            )
            from PIL import Image

            with Image.open(path) as im:
                w, h = im.size
            groups = {}
            for token in tokens:
                if token["level"] == "5" and token["text"].strip():
                    key = tuple(token[k] for k in ["block_num", "par_num", "line_num"])
                    groups.setdefault(key, []).append(token)
            lines = []
            for key, words in groups.items():
                x0 = min(int(t["left"]) for t in words) / w
                y0 = min(int(t["top"]) for t in words) / h
                x1 = max(int(t["left"]) + int(t["width"]) for t in words) / w
                y1 = max(int(t["top"]) + int(t["height"]) for t in words) / h
                lines.append(
                    dict(
                        text="".join(t["text"] for t in words),
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                        confidence=float(np.mean([float(t["conf"]) for t in words]))
                        / 100,
                        block=key[0],
                    )
                )
            return path.stem, {"platform_box": box, "lines": lines}

        with ThreadPoolExecutor(max_workers=5) as pool:
            for card, result in pool.map(recognize, jobs):
                results[card] = result
    assert len(results) == len(rows)
    target = root / "data/processed/bulletin_embeddings_2026_ocr.json"
    target.write_text(json.dumps(results, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(results)} cards saved to {target}")


if __name__ == "__main__":
    extract(Path(__file__).resolve().parents[2])
