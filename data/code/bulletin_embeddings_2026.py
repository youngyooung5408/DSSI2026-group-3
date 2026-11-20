"""2026-only bulletin corpus and BGE-M3 baseline. Run via paired notebook.
Segments are punctuation-delimited text, NOT validated independent proposals.
"""

from pathlib import Path
import hashlib, json, re, os, platform, importlib.metadata
import numpy as np
import pandas as pd

MODEL_ID = "BAAI/bge-m3"
INPUTS = {
    "data/processed/bulletin_embeddings_2026_ocr.json": "b1ee816896056cbd56729a48ab1d0eff671ef97e12014fe97c9e698f272891af",
    "data/processed/candidate_bulletin_2026.csv": "d2e1c4d5f9d7ef8266ffefd3f5f853eeda35f2174692c03f59b371713adafc7b",
    "data/processed/bulletin_2026_cards_ocr.json": "4b032748914700f2928e89589481f11261a7b5ca7db500c6d577d1312e8bc563",
    "data/raw/cec_bulletin_2026/file_manifest.json": "3d1dc56485df2be41b12c53732a2cc21be5464519d6fb02e332ea60d3f9f0aea",
}
STEM = "bulletin_embeddings_2026"


def root():
    for p in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (p / "AGENTS.md").is_file() and (p / "templates").is_dir():
            return p
    raise FileNotFoundError("Run inside project")


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    return re.sub(r"\s+", "", s)


def normalize(s):
    # Preserve wording, punctuation and negation; join layout wraps only.
    return re.sub(r"\s+", " ", s).strip()


def segments(text):
    # Keep semantically uncertain commas and enumeration marks intact.
    # Decimal points and ASCII periods are deliberately not delimiters.
    # Keep source offsets, splitting before visible bullets and numbered items.
    marker = r"(?m)^[ \t]*(?:[·●○•◎口囗□▪◆★☑]|[（(]?[一二三四五六七八九十百0-9０-９]{1,3}[）).．、·])"
    boundaries = {0, len(text)}
    boundaries.update(match.start() for match in re.finditer(marker, text))
    boundaries.update(match.end() for match in re.finditer(r"\n\s*\n", text))
    boundaries.update(match.end() for match in re.finditer(r"[。！？；!?;]+", text))
    boundaries = sorted(boundaries)
    out = []
    for a, b in zip(boundaries, boundaries[1:]):
        raw = text[a:b]
        clean = normalize(raw)
        if clean and clean != "政見" and re.search(r"[\w㐀-鿿]", clean):
            out.append((a, b, raw, clean))
    return out


def read_layout(lines):
    """Split spatial blocks at clear gutters, then keep top-to-bottom lines."""
    if not lines:
        return ""

    def blocks(items):
        if len(items) < 3:
            return [items]
        heights = [q["y1"] - q["y0"] for q in items]
        for low, high, threshold in [
            ("x0", "x1", 0.015),
            ("y0", "y1", max(0.012, float(np.median(heights)) * 0.8)),
        ]:
            ordered = sorted(items, key=lambda q: q[low])
            splits = []
            end = ordered[0][high]
            for i, line in enumerate(ordered[1:], 1):
                if line[low] - end > threshold:
                    splits.append((line[low] - end, i))
                end = max(end, line[high])
            if splits:
                _, i = max(splits)
                return blocks(ordered[:i]) + blocks(ordered[i:])
        return [items]

    return "\n\n".join(
        "\n".join(
            line["text"] for line in sorted(group, key=lambda q: (q["y0"], q["x0"]))
        )
        for group in blocks(lines)
    )


def han_count(text):
    return len(re.findall(r"[㐀-鿿]", text))


def prepare(r):
    for name, h in INPUTS.items():
        assert sha(r / name) == h, f"Input changed: {name}"
    df = pd.read_csv(
        r / "data/processed/candidate_bulletin_2026.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    assert len(df) == 280 and df.candidate_key.is_unique
    assert df.candidate_key.str.startswith("2026").all()
    evidence = json.loads(
        (r / "data/processed/bulletin_2026_cards_ocr.json").read_text()
    )
    manifest = json.loads(
        (r / "data/raw/cec_bulletin_2026/file_manifest.json").read_text()
    )
    for m in manifest:
        p = (r / m["path"]).resolve()
        assert p.is_relative_to((r / "data/raw/cec_bulletin_2026").resolve())
        assert "/115/" in m["source_url"] or "115" in m.get("source_path", ""), m[
            "path"
        ]
        assert sha(p) == m["sha256"], m["path"]
    reference = {m["path"]: m for m in manifest}
    matched = df[df.card_id.ne("")]
    assert len(matched) == 279 and matched.card_id.is_unique
    assert set(matched.card_id) == set(evidence)
    assert df.loc[df.card_id.eq(""), "platform_text"].eq("").all()
    for _, row in matched.iterrows():
        pdf_meta = reference[row.file]
        assert (
            row.source_sha256 == pdf_meta["sha256"]
            and row.source_url == pdf_meta["source_url"]
        )
        assert int(float(row.page)) >= 1
        ev = evidence[row.card_id]["platform"]
        text = (
            ev["text_layer"]
            if row.platform_source == "text_layer"
            else "".join(
                x["text"]
                for x in sorted(ev["ocr_lines"], key=lambda x: (x["y"], x["x"]))
            )
        )
        assert norm(text) == norm(row.platform_text), row.candidate_key
    keep = [
        "candidate_key",
        "candidate_name",
        "county_city",
        "office_type",
        "platform_text",
        "platform_source",
        "platform_image_share",
        "file",
        "source_url",
        "source_sha256",
        "page",
        "card_bbox",
        "card_id",
        "bulletin_status",
        "bulletin_note",
        "match_method",
    ]
    corpus = df[keep].copy()
    corpus["election_year"] = 2026
    image_readings = json.loads(
        (r / "data/processed/bulletin_embeddings_2026_ocr.json").read_text()
    )
    assert set(image_readings) == set(
        corpus.loc[corpus.platform_source.eq("ocr"), "card_id"]
    )
    corpus["upstream_platform_text"] = corpus.platform_text
    corpus["selected_reading"] = corpus.platform_source
    for idx, row in corpus[corpus.platform_source.eq("ocr")].iterrows():
        alternative = read_layout(image_readings[row.card_id]["lines"])
        # More recognized characters are a coverage heuristic, not an accuracy score.
        if han_count(alternative) >= max(8, han_count(row.platform_text) * 1.5):
            corpus.at[idx, "platform_text"] = alternative
            corpus.at[idx, "selected_reading"] = "tesseract_ocr"
    from difflib import SequenceMatcher

    corpus["ocr_agreement"] = pd.Series(index=corpus.index, dtype="float64")
    for idx, row in corpus[corpus.platform_source.eq("ocr")].iterrows():
        a = re.sub(r"[^㐀-鿿]", "", row.upstream_platform_text)
        b = re.sub(r"[^㐀-鿿]", "", read_layout(image_readings[row.card_id]["lines"]))
        corpus.at[idx, "ocr_agreement"] = SequenceMatcher(
            None, a, b, autojunk=False
        ).ratio()
    corpus["review_priority"] = np.where(corpus.ocr_agreement.lt(0.50), "high_ocr_disagreement", "standard")
    corpus.loc[corpus.platform_text.eq(""), "review_priority"] = "no_bulletin"
    corpus["embedding_text"] = corpus.platform_text.map(normalize)
    corpus["extraction_review_status"] = np.where(
        corpus.platform_source.eq("ocr"), "ocr_unreviewed", "text_layer_unreviewed"
    )
    corpus.loc[corpus.platform_text.eq(""), "extraction_review_status"] = (
        "not_available"
    )
    corpus["text_sha256"] = corpus.platform_text.map(
        lambda s: hashlib.sha256(s.encode()).hexdigest()
    )
    rows = []
    for _, row in corpus.iterrows():
        for i, (a, b, raw, text) in enumerate(segments(row.platform_text)):
            rows.append(
                {
                    "segment_id": f"{row.candidate_key}::seg{i + 1:03d}",
                    "candidate_key": row.candidate_key,
                    "candidate_name": row.candidate_name,
                    "segment_number": i + 1,
                    "char_start": a,
                    "char_end": b,
                    "text_original": raw,
                    "embedding_text": text,
                    "platform_source": row.platform_source,
                    "selected_reading": row.selected_reading,
                    "source_url": row.source_url,
                    "page": row.page,
                    "card_id": row.card_id,
                    "segmentation_status": "provisional_segment",
                    "topic": "",
                    "subtopic": "",
                    "stance": "",
                    "scope": "",
                    "label_status": "not_coded",
                }
            )
    seg = pd.DataFrame(rows)
    assert seg.segment_id.is_unique
    return corpus, seg, manifest


def csv_save(df, p):
    df.to_csv(p, index=False, encoding="utf-8-sig")
    saved = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert len(saved) == len(df) and list(saved) == list(df)


def run(model_revision=None):
    from sentence_transformers import SentenceTransformer
    import torch

    r = root()
    out = r / "data/processed"
    corpus, seg, manifest = prepare(r)
    revision = model_revision or "5617a9f61b028005a4858fdac845db406aefb181"
    assert revision and len(revision) == 40
    # Save float32 vectors and record the inference device.
    torch.set_num_threads(min(6, os.cpu_count() or 1))
    local_model = os.environ.get("DSSI_BGE_MODEL_DIR")
    if local_model:
        assert (
            sha(Path(local_model) / "pytorch_model.bin")
            == "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38"
        )
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer(
        local_model or MODEL_ID,
        revision=None if local_model else revision,
        device=device,
    )
    assert model.get_sentence_embedding_dimension() == 1024
    model.max_seq_length = 8192
    available = corpus[corpus.embedding_text.ne("")].copy().reset_index(drop=True)

    def embed(frame):
        texts = frame.embedding_text.tolist()
        lengths = [
            len(x)
            for x in model.tokenizer(texts, add_special_tokens=True, truncation=False)[
                "input_ids"
            ]
        ]
        assert max(lengths) <= 8192, "Oversized input: do not silently truncate"
        frame["token_count"] = lengths
        frame["embedding_row"] = range(len(frame))
        vectors = model.encode(
            texts,
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype("float32")
        assert vectors.shape == (len(frame), 1024) and np.isfinite(vectors).all()
        assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
        return vectors

    print("Embedding candidate policy sections:", len(available), flush=True)
    cv = embed(available)
    print("Embedding punctuation segments:", len(seg), flush=True)
    sv = embed(seg)
    corpus = corpus.merge(
        available[["candidate_key", "embedding_row", "token_count"]],
        on="candidate_key",
        how="left",
        validate="one_to_one",
    )
    corpus["embedding_row"] = corpus.embedding_row.astype("Int64")
    corpus["token_count"] = corpus.token_count.astype("Int64")
    paths = []
    for name, frame in [("corpus", corpus), ("segments", seg)]:
        p = out / f"{STEM}_{name}.csv"
        csv_save(frame, p)
        paths.append(p)
    for name, v in [("candidate", cv), ("segment", sv)]:
        p = out / f"{STEM}_{name}_vectors.npy"
        np.save(p, v, allow_pickle=False)
        assert np.array_equal(np.load(p, allow_pickle=False), v)
        paths.append(p)
    # Cross-candidate nearest neighbours; not duplicate decisions or topic labels.
    nn = []
    for start in range(0, len(seg), 256):
        sims = sv[start : start + 256] @ sv.T
        for k, scores in enumerate(sims):
            i = start + k
            scores[seg.candidate_key.to_numpy() == seg.iloc[i].candidate_key] = -np.inf
            j = int(np.argmax(scores))
            nn.append(
                {
                    "segment_id": seg.iloc[i].segment_id,
                    "candidate_key": seg.iloc[i].candidate_key,
                    "candidate_name": seg.iloc[i].candidate_name,
                    "text": seg.iloc[i].embedding_text,
                    "neighbor_segment_id": seg.iloc[j].segment_id,
                    "neighbor_candidate_key": seg.iloc[j].candidate_key,
                    "neighbor_candidate_name": seg.iloc[j].candidate_name,
                    "neighbor_text": seg.iloc[j].embedding_text,
                    "cosine_similarity": float(scores[j]),
                }
            )
    p = out / f"{STEM}_neighbors.csv"
    csv_save(pd.DataFrame(nn), p)
    paths.append(p)
    pairs = [
        ("同議題同立場", "支持重啟核電廠。", "贊成恢復核能發電。"),
        ("同議題反立場", "支持重啟核電廠。", "反對重啟核電廠。"),
        ("不同議題", "支持重啟核電廠。", "增設公共托育中心。"),
        ("同議題不同措施", "興建社會住宅。", "擴大租金補貼。"),
        ("同議題不同尺度", "改善本市公共運輸。", "改革全國公共運輸補助制度。"),
    ]
    pv = model.encode(
        [s for _, a, b in pairs for s in (a, b)],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    probes = pd.DataFrame(
        [
            dict(
                pair_type=t,
                text_a=a,
                text_b=b,
                cosine_similarity=float(pv[i * 2] @ pv[i * 2 + 1]),
                source="synthetic_diagnostic_not_bulletin",
            )
            for i, (t, a, b) in enumerate(pairs)
        ]
    )
    p = out / f"{STEM}_diagnostics.csv"
    csv_save(probes, p)
    paths.append(p)
    config = {
        "model_id": MODEL_ID,
        "revision": revision,
        "dimensions": 1024,
        "max_sequence_tokens": 8192,
        "batch_size": 8,
        "device": device,
        "dtype": "float32",
        "normalize_embeddings": True,
        "similarity": "cosine",
        "prompt": None,
        "segmentation": "bullet and punctuation v2: 。！？；!?; boundaries; layout whitespace collapsed; commas/newlines not split",
        "scope": "2026 only; 81 chiefs + 199 Taipei/Kaohsiung council candidates",
        "input_hashes": INPUTS,
        "manifest_pdf_count": len(manifest),
        "candidate_count": len(corpus),
        "embedded_candidates": len(cv),
        "segment_count": len(seg),
        "selected_reading_counts": corpus.selected_reading.value_counts().to_dict(),
        "extraction_source_counts": corpus.platform_source.value_counts().to_dict(),
        "candidate_token_range": [
            int(available.token_count.min()),
            int(available.token_count.max()),
        ],
        "segment_token_range": [int(seg.token_count.min()), int(seg.token_count.max())],
        "packages": {
            x: importlib.metadata.version(x)
            for x in [
                "sentence-transformers",
                "transformers",
                "torch",
                "numpy",
                "pandas",
                "huggingface-hub",
            ]
        },
        "python": platform.python_version(),
        "output_hashes": {str(p.relative_to(r)): sha(p) for p in paths},
        "limitations": [
            "OCR not fully visually verified; designed multi-column reading order can be mixed",
            "Segments may contain several proposals or slogans; cannot be treated as S5 units",
            "Topic/stance/scope unlabelled; S5/S6/S7/S10 not yet calculated",
            "Nearest neighbors are exploratory; no validated similarity threshold",
            "Whole-section vectors can conceal topic distribution",
        ],
    }
    p = out / f"{STEM}_run.json"
    p.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    assert json.loads(p.read_text()) == config
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print(probes.to_string(index=False))
    return config


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--revision")
    args = ap.parse_args()
    run(args.revision)
