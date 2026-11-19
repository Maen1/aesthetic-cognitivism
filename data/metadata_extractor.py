#!/usr/bin/env python3
"""
metadata_extractor.py
vLLM batch inference & regex concept/snippet extraction pipeline for Aesthetic Cognitivism.
Extracts artists/creators (excluding the review's critic/author), artform category,
sentiment, summary, and 273 aesthetic concept snippets into JSONL chunks.
"""

import argparse
import json
import os
import re
import time

import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

# Optional vLLM structured output / guided JSON support (enabled via --guided-json)
try:
    from pydantic import BaseModel
    from typing import Dict, Literal
    try:
        from vllm.sampling_params import StructuredOutputsParams
        STRUCTURED_PARAM_CLS = ("structured_outputs", StructuredOutputsParams)
    except ImportError:
        try:
            from vllm.sampling_params import GuidedDecodingParams
            STRUCTURED_PARAM_CLS = ("guided_decoding", GuidedDecodingParams)
        except ImportError:
            STRUCTURED_PARAM_CLS = None

    class CritiqueMetadata(BaseModel):
        artists: Dict[str, int]
        category: Literal[
            "Theater", "Concerts", "Exhibitions", "Movies",
            "Opera", "Dance", "Literature", "Television", "Radio",
            "Mixed", "Unknown"
        ]
        sentiment: Literal["Positive", "Negative", "Neutral", "Mixed"]
        summary: str

    JSON_SCHEMA = CritiqueMetadata.model_json_schema()
except ImportError:
    STRUCTURED_PARAM_CLS = None
    JSON_SCHEMA = None


# --- Configuration ---
MODEL_NAME = os.environ.get(
    "HF_MODEL",
    "/dataset/easybuild/data/openai-gpt-oss-120b-model/20250826-hf"
)
INITIAL_BATCH_SIZE = 512   # Keeps H200 continuous batching saturated
MAX_BATCH_SIZE = 1024
MAX_SEQUENCE_LENGTH = 8192
MAX_INPUT_TOKENS = 5500    # Leaves headroom for system/prompt wrapper + 2048 output tokens

BASE_DIR = "/nobackup/proj/disk/naiss2025-22-1370/personal/adammae"
input_jsonl_paths = [
    f"{BASE_DIR}/extracted_art_critics.jsonl",
    f"{BASE_DIR}/extracted_art_critics2.jsonl",
    f"{BASE_DIR}/extracted_art_critics3.jsonl",
]

# --- Vocabulary & Concept Mapping ---
word_list = [
    "absorbing", "abstract", "acclaimed", "accomplished",
    "accurate", "adept", "adroit", "aggressive", "agile", "agreeable",
    "ambiguous", "angry", "anxious", "astonishing", "astringent", "atmospheric",
    "attractive", "audacious", "authentic", "avant-garde", "awesome",
    "backward-looking", "bad", "baffling", "balanced", "baroque", "beautiful",
    "bittersweet", "boisterous", "boistrous", "bold", "boring", "breathtaking",
    "bright", "brilliant", "candid", "careful", "catchy", "challenging",
    "charming", "cheerful", "classical", "clean", "clever", "clumsy", "coarse",
    "coherent", "comely", "comic", "compassionate", "compelling", "complex",
    "confusing", "consoling", "consummate", "contemplative", "contemporary",
    "controversial", "convincing", "cool", "creative", "dainty", "dappled",
    "daring", "dark", "dated", "dazzling", "deft", "delicate", "delightful",
    "depressing", "derivative", "despressing", "diffuse", "disciplined",
    "disciplines", "disorganised", "disorganized", "displeasing", "dissonant",
    "dramatic", "dreamlike", "dynamic", "earthy", "economical", "efficient",
    "effiecient", "elegant", "eloquent", "elusive", "energetic", "enigmatic",
    "enjoyable", "enlightening", "ethereal", "etheral", "evocative", "exact",
    "expert", "expressionist", "expressive", "exquisite", "fair", "fine",
    "flawless", "flickering", "fluffy", "forward-looking", "garish", "generic",
    "genuine", "gifted", "glowing", "golden", "good", "gothic", "graceful",
    "gracious", "graiting", "grating", "ground-breaking", "handsome", "happy",
    "harmonic", "harmonious", "haunting", "hautning", "honest", "hopeful",
    "hopeless", "horrible", "human", "hypnotic", "illusion", "imaginative",
    "imitative", "impeccable", "impressionist", "impressive", "individual",
    "infinite", "infinte", "innovative", "insightful", "inspirational",
    "interesting", "intuitive", "joyful", "joyous", "jubilant", "layered",
    "lifelike", "limpid", "lively", "long-winded", "lousy", "luminous",
    "masterful", "masterly", "mature", "mediocre", "melancholic", "mellow",
    "melodic", "memorable", "modernist", "moist", "monochrome", "moving",
    "muddy", "muted", "mysterious", "naturalistic", "neoclassical", "newfangled",
    "noble", "nostalgic", "offputting", "old-fashioned", "organic", "original",
    "overwhelming", "painful", "pale", "paradoxical", "passionate", "pastel",
    "pathetic", "peaceful", "persuasive", "philosophical", "picturesque",
    "pleasing", "poetic", "poetical", "poignant", "polished", "postmodern",
    "powerful", "practiced", "practised", "precise", "pretentious", "pretty",
    "prickly", "profound", "promising", "radiant", "raw", "realistic",
    "refined", "relevant", "remarkable", "renaissance", "repetetive",
    "repetitive", "representational", "resonant", "revolutionary", "rhythmic",
    "rococo", "rococco", "romantic", "rough", "sad", "satin", "saturated",
    "saturrated", "scaly", "seamless", "sensual", "serene", "shaded",
    "shimmering", "shiny", "shrill", "skillful", "slippery", "smooth", "somber",
    "sophisticated", "sorrowful", "souldful", "soulful", "spiritual",
    "splendid", "stimulating", "strange", "strident", "striking", "stunning",
    "sublime", "subtle", "surreal", "surrealistic", "tasteful", "tender",
    "terrible", "textured", "thought-provoking", "through-composed", "timeless",
    "tragic", "tranquil", "transparent", "triumphant", "true", "ugly",
    "unified", "velvet", "verisimilitude", "versatile", "vibrant", "virtuosic",
    "vivid", "warm", "well-organised", "well-organized", "wonderful",
    "world-shattering", "worrying"
]

# Single compiled regex (matches longest words first) — ~50x faster than 280 separate scans
CANONICAL_WORDS = {w.lower(): w for w in word_list}
MASTER_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(w) for w in sorted(word_list, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

VALID_CATEGORIES = {
    "theater": "Theater",
    "theatre": "Theater",
    "concerts": "Concerts",
    "concert": "Concerts",
    "music": "Concerts",
    "exhibitions": "Exhibitions",
    "exhibition": "Exhibitions",
    "art": "Exhibitions",
    "movies": "Movies",
    "movie": "Movies",
    "film": "Movies",
    "films": "Movies",
    "cinema": "Movies",
    "opera": "Opera",
    "operas": "Opera",
    "dance": "Dance",
    "ballet": "Dance",
    "literature": "Literature",
    "poetry": "Literature",
    "books": "Literature",
    "book": "Literature",
    "television": "Television",
    "tv": "Television",
    "radio": "Radio",
    "mixed": "Mixed",
    "unknown": "Unknown",
}

VALID_SENTIMENTS = {
    "positive": "Positive",
    "negative": "Negative",
    "neutral": "Neutral",
    "mixed": "Mixed",
}


def extract_word_snippets(text):
    """Single-pass extraction of vocabulary words and 60-char context snippets."""
    if not isinstance(text, str) or not text:
        return [], {}

    found_concepts = []
    seen = set()
    snippets = {}

    for m in MASTER_PATTERN.finditer(text):
        word = CANONICAL_WORDS[m.group(0).lower()]
        if word not in seen:
            seen.add(word)
            found_concepts.append(word)
            snippets[word] = []
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 60)
        snippet = text[start:end].replace('\n', ' ').strip()
        snippets[word].append(f"...{snippet}...")

    return found_concepts, snippets


# --- Author & JSON Normalization Helpers ---
def build_author_aliases(author_raw):
    """Build normalized lowercase aliases of the critic's name (handles 'Last, First')."""
    if not isinstance(author_raw, str):
        return set()
    author = author_raw.strip()
    if not author or author.lower() in {"nan", "none", "null", "unknown"}:
        return set()

    aliases = {author.lower()}
    if "," in author:
        parts = [p.strip() for p in author.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            last, first = parts[0], parts[1]
            aliases.add(f"{first} {last}".lower())
            first_token = first.split()[0]
            if len(first_token) > 1:
                aliases.add(f"{first_token} {last}".lower())
    return aliases


def clean_artists_dict(artists_raw, author_raw):
    """Validate artist percentage dictionary and strip the article's critic/author."""
    if not isinstance(artists_raw, dict):
        return {}
    aliases = build_author_aliases(author_raw)
    cleaned = {}
    for k, v in artists_raw.items():
        if not k:
            continue
        name = str(k).strip()
        if not name or name.lower() in aliases:
            continue
        try:
            pct = float(v)
            if pct < 0:
                continue
            cleaned[name] = int(pct) if pct.is_integer() else round(pct, 2)
        except (TypeError, ValueError):
            continue
    return cleaned


def normalize_category(cat_raw):
    if not isinstance(cat_raw, str) or not cat_raw.strip():
        return "Unknown"
    c = cat_raw.strip()
    return VALID_CATEGORIES.get(c.lower(), c)


def normalize_sentiment(sent_raw):
    if not isinstance(sent_raw, str) or not sent_raw.strip():
        return "Neutral"
    s = sent_raw.strip().lower()
    if s in VALID_SENTIMENTS:
        return VALID_SENTIMENTS[s]
    if ("pos" in s and "neg" in s) or "mix" in s:
        return "Mixed"
    if "pos" in s:
        return "Positive"
    if "neg" in s:
        return "Negative"
    return "Neutral"


def extract_json_object(raw_text):
    """Extract the final JSON object cleanly from GPT-OSS Harmony channel output."""
    if not raw_text:
        return None
    if "<|channel|>final<|message|>" in raw_text:
        raw_text = raw_text.split("<|channel|>final<|message|>")[-1]
    raw_text = raw_text.replace("<|return|>", "").replace("<|end|>", "").strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(raw_text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for i, ch in enumerate(raw_text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(raw_text[i:])
                if isinstance(obj, dict) and ("category" in obj or "summary" in obj or "artists" in obj):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


# --- Checkpoint Management ---
def load_checkpoint(total_rows, checkpoint_file, output_jsonl_path):
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            actual_lines = 0
            if os.path.exists(output_jsonl_path):
                with open(output_jsonl_path, 'r', encoding='utf-8') as f_out:
                    actual_lines = sum(1 for _ in f_out)

            processed = min(checkpoint.get("processed", 0), actual_lines)
            print(f"🔄 Resuming from checkpoint: {processed}/{total_rows} rows processed")
            return processed, checkpoint.get("batch_size", INITIAL_BATCH_SIZE)
        except Exception as e:
            print(f"⚠️ Error loading checkpoint: {e}")
    return 0, INITIAL_BATCH_SIZE


def save_checkpoint(processed_count, batch_size, checkpoint_file):
    checkpoint = {
        "processed": processed_count,
        "batch_size": batch_size,
        "timestamp": time.time()
    }
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
    except Exception as e:
        print(f"⚠️ Error saving checkpoint: {e}")


# --- Initialize vLLM Model ---
def initialize_model():
    gpu_env = os.environ.get("SLURM_GPUS_ON_NODE", "")
    tp_size = int(gpu_env) if gpu_env.isdigit() else (torch.cuda.device_count() or 1)
    print(f"Initializing vLLM model with tensor_parallel_size={tp_size}...")
    try:
        llm = LLM(
            model=MODEL_NAME,
            tensor_parallel_size=tp_size,
            gpu_memory_utilization=0.92,
            max_model_len=MAX_SEQUENCE_LENGTH,
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        print(f"✅ Successfully loaded model: {MODEL_NAME}")
        return llm, tokenizer
    except Exception as e:
        print(f"❌ Error loading vLLM model: {e}")
        exit(1)


# --- Prompt & Sampling Builders ---
def truncate_text_safely(text, tokenizer):
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    if len(cleaned) <= 12000:
        return cleaned
    # Fast character pre-cap before token check
    if len(cleaned) > 30000:
        cleaned = cleaned[:30000]
    token_ids = tokenizer.encode(cleaned, add_special_tokens=False)
    if len(token_ids) > MAX_INPUT_TOKENS:
        cleaned = tokenizer.decode(token_ids[:MAX_INPUT_TOKENS], skip_special_tokens=True) + " ...[truncated]"
    return cleaned


def build_prompt(full_text, title, author, tokenizer):
    cleaned_text = truncate_text_safely(full_text, tokenizer)
    title_str = str(title).strip() if isinstance(title, str) and title.strip() and title.strip().lower() != "nan" else "Untitled"
    author_str = str(author).strip() if isinstance(author, str) and author.strip() and author.strip().lower() != "nan" else "Unknown"

    messages = [
        {
            "role": "system",
            "content": "You are an expert art and culture critic analyst. Extract structured information from critiques. Output strictly in JSON format. Reasoning: low"
        },
        {
            "role": "user",
            "content": f"""Analyze this article/critique and extract:
1. EVERY artist, performer, composer, playwright, director, actor, or creator discussed in the work (use full canonical names where unambiguous, e.g., "Ludwig van Beethoven" instead of "Beethoven"), and the estimated percentage of the text dedicated to them. Do NOT include the critic, reviewer, or journalist who wrote the article (Article Author: {author_str}).
2. The single best art category from ONLY this list:
   - "Theater" (stage plays, drama, theatre reviews/listings)
   - "Concerts" (classical/jazz/rock/pop concerts, recitals, music albums)
   - "Exhibitions" (art galleries, museums, painting, sculpture, photography, architecture)
   - "Movies" (films, cinema)
   - "Opera" (opera, operetta)
   - "Dance" (ballet, modern dance)
   - "Literature" (books, novels, fiction, poetry, literary criticism)
   - "Television" (TV reviews, TV guides/choices)
   - "Radio" (radio broadcasts, radio choices)
   - "Mixed" (arts festival or column covering multiple distinct art forms equally)
   - "Unknown" (ONLY if the article is not about arts/culture at all)
3. The sentiment of the critique ("Positive", "Negative", "Neutral", or "Mixed").
4. A concise 1-2 sentence summary (never output "N/A" unless the text is completely unreadable).

Respond ONLY with a valid JSON object matching this exact structure. Do not include markdown code blocks or any extra text:
{{
  "artists": {{"Full Artist Name": 20, "Another Artist": 15}},
  "category": "Category",
  "sentiment": "Positive",
  "summary": "Your summary here"
}}

If zero specific artists/creators are discussed, leave "artists" empty ({{}}).

Title: {title_str}
Author (critic - exclude from artists): {author_str}
Text: {cleaned_text}"""
        }
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def make_sampling_params(max_tokens=2048, use_guided_json=False):
    kwargs = {"temperature": 0.0, "max_tokens": max_tokens}
    if use_guided_json and STRUCTURED_PARAM_CLS is not None and JSON_SCHEMA is not None:
        param_key, param_cls = STRUCTURED_PARAM_CLS
        kwargs[param_key] = param_cls(json=JSON_SCHEMA)
    return SamplingParams(**kwargs)


# --- LLM Processing Function ---
def get_metadata_llm(text_list, title_list, author_list, llm, tokenizer, use_guided_json=False):
    prompts = []
    original_indices = []

    for idx, (full_text, title, author) in enumerate(zip(text_list, title_list, author_list)):
        if isinstance(full_text, str) and full_text.strip():
            prompts.append(build_prompt(full_text, title, author, tokenizer))
            original_indices.append(idx)

    final_artists = [{} for _ in range(len(text_list))]
    final_categories = ["Unknown"] * len(text_list)
    final_sentiments = ["Neutral"] * len(text_list)
    final_summaries = ["N/A"] * len(text_list)

    if not prompts:
        return final_artists, final_categories, final_sentiments, final_summaries

    def apply_parsed(orig_idx, parsed_data):
        final_artists[orig_idx] = clean_artists_dict(parsed_data.get("artists", {}), author_list[orig_idx])
        final_categories[orig_idx] = normalize_category(parsed_data.get("category", "Unknown"))
        final_sentiments[orig_idx] = normalize_sentiment(parsed_data.get("sentiment", "Neutral"))
        summ = parsed_data.get("summary")
        final_summaries[orig_idx] = str(summ).strip() if summ and str(summ).strip() else "N/A"

    try:
        sampling_params = make_sampling_params(max_tokens=2048, use_guided_json=use_guided_json)
        outputs = llm.generate(prompts, sampling_params, use_tqdm=False)

        retry_indices = []
        retry_prompts = []

        for idx, output in enumerate(outputs):
            orig_idx = original_indices[idx]
            parsed_data = extract_json_object(output.outputs[0].text.strip())
            if parsed_data is not None:
                apply_parsed(orig_idx, parsed_data)
            else:
                retry_indices.append(orig_idx)
                retry_prompts.append(prompts[idx])

        # Retry any truncated/malformed rows once with a higher token budget (4096)
        if retry_prompts:
            retry_params = make_sampling_params(max_tokens=4096, use_guided_json=use_guided_json)
            retry_outputs = llm.generate(retry_prompts, retry_params, use_tqdm=False)
            parse_failures = 0
            for orig_idx, output in zip(retry_indices, retry_outputs):
                parsed_data = extract_json_object(output.outputs[0].text.strip())
                if parsed_data is not None:
                    apply_parsed(orig_idx, parsed_data)
                else:
                    parse_failures += 1

            if parse_failures > 0:
                print(f"⚠️ JSON parse failed after retry on {parse_failures}/{len(outputs)} rows in this batch.")

        return final_artists, final_categories, final_sentiments, final_summaries

    except torch.cuda.OutOfMemoryError as e:
        print(f"⚠️ CUDA OOM during vLLM generation: {e}")
        return None, None, None, None
    except Exception as e:
        err_msg = str(e).lower()
        if "out of memory" in err_msg or "cuda" in err_msg or "kv cache" in err_msg:
            print(f"⚠️ vLLM memory error: {e}")
            return None, None, None, None
        raise


# --- Main Processing Loop ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-id", type=int, default=0)
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument(
        "--guided-json",
        action="store_true",
        help="Enable vLLM structured/guided JSON decoding if compatible with model chat template."
    )
    args = parser.parse_args()

    output_jsonl_path = f"{BASE_DIR}/final_analyzed_critics_part{args.chunk_id}.jsonl"
    checkpoint_file = f"{BASE_DIR}/analysis_checkpoint_part{args.chunk_id}.json"

    llm, tokenizer = initialize_model()

    print("Loading JSONL files...")
    dfs = []
    for path in input_jsonl_paths:
        if os.path.exists(path):
            print(f"  Reading {path}...")
            dfs.append(pd.read_json(path, lines=True))
    if not dfs:
        print("❌ No JSONL files found!")
        return

    df = pd.concat(dfs, ignore_index=True)

    # Unify text column across all 3 JSONL files (handling both NaN and empty strings)
    if 'extracted_text' in df.columns and 'Full_text' in df.columns:
        empty_mask = df['extracted_text'].isna() | (df['extracted_text'].astype(str).str.strip() == '')
        df.loc[empty_mask, 'extracted_text'] = df.loc[empty_mask, 'Full_text']
    elif 'Full_text' in df.columns:
        df['extracted_text'] = df['Full_text']

    # Slice this worker's chunk
    total_all = len(df)
    chunk_size = (total_all + args.num_chunks - 1) // args.num_chunks
    slice_start = args.chunk_id * chunk_size
    slice_end = min(slice_start + chunk_size, total_all)
    df = df.iloc[slice_start:slice_end].reset_index(drop=True)

    total_rows = len(df)
    print(f"📦 Chunk {args.chunk_id}/{args.num_chunks}: rows {slice_start}..{slice_end} ({total_rows} rows)")

    start_index, current_batch_size = load_checkpoint(total_rows, checkpoint_file, output_jsonl_path)
    i = start_index
    consecutive_successes = 0

    mode = 'a' if start_index > 0 else 'w'
    with open(output_jsonl_path, mode, encoding='utf-8') as f_out:
        with tqdm(total=total_rows, initial=start_index, desc=f"Chunk {args.chunk_id}") as pbar:
            while i < total_rows:
                end_index = min(i + current_batch_size, total_rows)
                batch_df = df.iloc[i:end_index].copy()
                text_batch = batch_df['extracted_text'].tolist()
                title_batch = batch_df['Title'].tolist() if 'Title' in batch_df.columns else [None] * len(text_batch)
                author_batch = batch_df['Author'].tolist() if 'Author' in batch_df.columns else [None] * len(text_batch)

                # 1. Single-Pass Regex Snippets
                batch_concepts = []
                batch_snippets = []
                for text in text_batch:
                    concepts, snippets = extract_word_snippets(text)
                    batch_concepts.append(concepts)
                    batch_snippets.append(snippets)

                # 2. LLM Inference
                artists, categories, sentiments, summaries = get_metadata_llm(
                    text_batch,
                    title_batch,
                    author_batch,
                    llm,
                    tokenizer,
                    use_guided_json=args.guided_json,
                )

                if artists is None:
                    if current_batch_size > 1:
                        current_batch_size = max(1, current_batch_size // 2)
                        print(f"📉 OOM: Reducing batch size to {current_batch_size}")
                        continue
                    else:
                        print("❌ Fatal OOM at batch size 1.")
                        break

                batch_df['LLM_Artists_Percentages'] = artists
                batch_df['Category'] = categories
                batch_df['Sentiment'] = sentiments
                batch_df['Summary'] = summaries
                batch_df['Found_Concepts'] = batch_concepts
                batch_df['Concept_Snippets'] = batch_snippets

                for _, row in batch_df.iterrows():
                    f_out.write(row.dropna().to_json() + '\n')
                f_out.flush()

                i = end_index
                pbar.update(len(batch_df))
                save_checkpoint(i, current_batch_size, checkpoint_file)

                consecutive_successes += 1
                if consecutive_successes >= 3 and current_batch_size < MAX_BATCH_SIZE:
                    current_batch_size = min(MAX_BATCH_SIZE, current_batch_size + 64)
                    consecutive_successes = 0

    print(f"✅ Chunk {args.chunk_id} saved to: {output_jsonl_path}")


if __name__ == "__main__":
    main()
