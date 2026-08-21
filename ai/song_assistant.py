# -*- coding: utf-8 -*-
"""Local Translator model helper for Minimaxmusic3.

Adapted from NDmusic's local lyric_writer.py flow. The helper is intentionally
one-shot: it loads the Translator model, fills/normalizes the requested song metadata, prints one JSON
object to stdout, and exits so VRAM is returned before MiniMax Music 3 starts inference.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Windows may use an ANSI code page for redirected Python pipes. Chinese lyrics
# would then fail with UnicodeEncodeError ('charmap'). Force UTF-8 end-to-end.
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="strict")
    except (AttributeError, ValueError):
        pass

DEFAULT_GGUF_NAME = "gemma-4-12b-it-qat-q4_0.gguf"
_LLM = None


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def _clean_lyrics(text: str) -> str:
    t = _strip_think(text)
    t = re.sub(r"```[a-zA-Z]*", "", t).replace("```", "")
    lines = [ln.rstrip() for ln in t.splitlines()]
    while lines and (
        not lines[0].strip()
        or re.match(r"^\s*(here (are|is)|sure|of course|okay|certainly)\b", lines[0], re.I)
    ):
        lines.pop(0)
    out = "\n".join(lines).strip()
    out = re.sub(
        r"^\s*\[?\s*(verse|chorus|bridge|intro|outro|pre[- ]?chorus|post[- ]?chorus|hook|solo|instrumental)\s*(\d*)\s*\]?\s*:?\s*$",
        lambda m: f"[{m.group(1).lower().replace(' ', '-')}{(' ' + m.group(2)) if m.group(2) else ''}]",
        out,
        flags=re.I | re.M,
    )
    return out.strip()


def _model_path() -> Path:
    raw = os.environ.get("GEMMA4_MT_GGUF", "").strip()
    if raw:
        p = Path(os.path.expandvars(raw)).expanduser()
        if p.is_file():
            return p
        if p.is_dir():
            files = sorted(
                [x for x in p.rglob("*.gguf") if x.is_file() and not x.name.lower().startswith("mmproj")],
                key=lambda x: x.stat().st_size,
                reverse=True,
            )
            if files:
                return files[0]
    raise RuntimeError(
        "Translator model not found. Download it in the Models tab or set GEMMA4_MT_GGUF."
    )


def _gpu_layers() -> int:
    raw = os.environ.get("GEMMA4_GPU_LAYERS", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return -1


def _chat(system: str, user: str, max_tokens: int = 1500, temperature: float = 0.72) -> str:
    global _LLM
    try:
        from llama_cpp import Llama
    except Exception as exc:
        raise RuntimeError(
            "The local Translator runtime is not installed. Run install.bat again."
        ) from exc

    if _LLM is None:
        _LLM = Llama(
            model_path=str(_model_path()),
            n_ctx=8192,
            n_gpu_layers=_gpu_layers(),
            verbose=False,
        )
    result = _LLM.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        top_k=60,
        repeat_penalty=1.08,
    )
    return _strip_think((result["choices"][0]["message"]["content"] or "").strip())


def _repair_json_escapes(raw: str) -> str:
    """Best-effort repair for legacy model JSON containing illegal backslash escapes.

    JSON only permits a small set of escape sequences. Song lyrics commonly contain
    a stray backslash before punctuation/letters, which makes json.loads() reject the
    entire response. Preserve valid escapes and double only invalid backslashes.
    """
    return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)


def _extract_legacy_json(text: str) -> dict[str, Any]:
    """Compatibility parser for responses from older prompts."""
    t = _strip_think(text)
    t = re.sub(r"```(?:json)?", "", t, flags=re.I).replace("```", "").strip()
    start = t.find("{")
    end = t.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("Translator model returned an invalid song plan.")
    raw = t[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Retry once after repairing illegal escape sequences such as \s, \', \-.
        try:
            data = json.loads(_repair_json_escapes(raw))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Translator model returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Translator model returned an invalid song plan.")
    return data


_FIELD_MARKERS = (
    "<<<MM3_TITLE>>>",
    "<<<MM3_STYLE>>>",
    "<<<MM3_LYRICS>>>",
    "<<<MM3_END>>>",
)


def _extract_song_fields(text: str) -> dict[str, Any]:
    """Parse the model response without requiring JSON escaping.

    v0.1.16 uses sentinel sections because lyrics are arbitrary free-form text and
    JSON is unnecessarily fragile (quotes, slashes and backslashes are common in
    songs). If the model ignores the new format, keep a repaired JSON fallback for
    compatibility with earlier prompts/models.
    """
    t = _strip_think(text)
    t = re.sub(r"```(?:text|txt|json)?", "", t, flags=re.I).replace("```", "").strip()
    title_m, style_m, lyrics_m, end_m = _FIELD_MARKERS
    if all(marker in t for marker in (title_m, style_m, lyrics_m)):
        title_start = t.find(title_m) + len(title_m)
        style_pos = t.find(style_m, title_start)
        lyrics_pos = t.find(lyrics_m, style_pos + len(style_m))
        end_pos = t.find(end_m, lyrics_pos + len(lyrics_m))
        if end_pos < 0:
            end_pos = len(t)
        if style_pos > title_start and lyrics_pos > style_pos:
            return {
                "title": t[title_start:style_pos].strip(),
                "style": t[style_pos + len(style_m):lyrics_pos].strip(),
                "lyrics": t[lyrics_pos + len(lyrics_m):end_pos].strip(),
            }
    return _extract_legacy_json(t)


def _vocal_instruction(mode: str) -> str:
    return {
        "male": (
            "The UI voice selection is a hard prompt constraint: use one adult MALE lead singer only. "
            "Describe a clearly masculine tenor-to-baritone identity, natural phrasing and stable timbre. "
            "Do not mention or request any female lead, female backing vocal, duet, or female spoken voice."
        ),
        "female": (
            "The UI voice selection is a hard prompt constraint: use one adult FEMALE lead singer only. "
            "Describe a clearly feminine mezzo-soprano-to-light-alto identity, natural phrasing and stable timbre. "
            "Do not mention or request any male lead, male backing vocal, duet, baritone, tenor, or male spoken voice."
        ),
        "duet": (
            "Use two clearly distinct adult lead singers, one female and one male. Alternate lead lines in verses "
            "and make both singers clearly audible together in choruses with complementary harmony. Do not collapse to one singer."
        ),
        "choir": (
            "Use a mixed male/female ensemble or choir with layered harmonies and no single dominant solo vocalist."
        ),
        "auto": "Choose the vocal character that best fits the song.",
    }.get(mode, "Choose the vocal character that best fits the song.")


def _contains_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in (text or ""))


def _contains_vietnamese(text: str) -> bool:
    # A light sanity check: natural Vietnamese lyrics normally contain either Đ/đ
    # or one of the language-specific vowel/diacritic characters below.
    return bool(re.search(r"[ăâđêôơưĂÂĐÊÔƠƯàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", text or "", re.I))


def _force_selected_language(title: str, style: str, lyrics: str, language: str, instruction: str) -> tuple[str, str, str]:
    if language == "chinese":
        if _contains_han(title) and _contains_han(lyrics):
            return title, style, lyrics
        editor_role = "strict Mandarin Chinese lyric editor"
        title_rule = "The TITLE and every sung lyric line MUST be Simplified Chinese suitable for natural Mandarin singing."
        exclusions = "Do not leave English lyric sentences, romanization, pinyin, commentary, or translation notes."
        rewrite = "Rewrite the title and lyrics now into natural Simplified Chinese / Mandarin. Preserve song structure and meaning."
        verify = lambda t, l: _contains_han(t) and _contains_han(l)
        error = "Translator could not produce Simplified Chinese lyrics. Try AI Fill again."
    elif language == "vietnamese":
        if _contains_vietnamese(title) and _contains_vietnamese(lyrics):
            return title, style, lyrics
        editor_role = "strict Vietnamese lyric editor"
        title_rule = "The TITLE and every sung lyric line MUST be natural modern Vietnamese with correct Vietnamese diacritics and singable phrasing."
        exclusions = "Do not translate the lyrics into Chinese or English. Do not remove Vietnamese diacritics, add romanization, commentary, or translation notes."
        rewrite = "Rewrite the title and lyrics now into natural Vietnamese with correct diacritics. Preserve song structure, emotion, and meaning."
        verify = lambda t, l: _contains_vietnamese(t) and _contains_vietnamese(l)
        error = "Translator could not produce Vietnamese lyrics. Try AI Fill again."
    else:
        return title, style, lyrics

    system = (
        f"You are a {editor_role}. Return ONLY the sentinel sections "
        "<<<MM3_TITLE>>>, <<<MM3_STYLE>>>, <<<MM3_LYRICS>>>, <<<MM3_END>>>. "
        f"{title_rule} "
        "Section tags such as [verse], [chorus], [bridge] stay in English inside square brackets. "
        f"{exclusions} "
        "The STYLE must remain English and preserve the supplied production description."
    )
    user = "\n".join([
        f"Original user intent: {instruction or '(none)'}",
        f"Current title: {title}",
        f"Current English style: {style}",
        f"Current lyrics:\n{lyrics}",
        rewrite,
    ])
    fixed = _extract_song_fields(_chat(system, user, max_tokens=1800, temperature=0.2))
    fixed_title = str(fixed.get("title") or title).strip()
    fixed_style = str(fixed.get("style") or style).strip()
    fixed_lyrics = _clean_lyrics(str(fixed.get("lyrics") or lyrics))
    if not verify(fixed_title, fixed_lyrics):
        raise RuntimeError(error)
    return fixed_title, fixed_style, fixed_lyrics


def build_song_plan(req: dict[str, Any]) -> dict[str, str]:
    instruction = str(req.get("instruction") or "").strip()
    title = str(req.get("title") or "").strip()
    if title.lower() == "untitled":
        title = ""
    style = str(req.get("style") or "").strip()
    lyrics = str(req.get("lyrics") or "").strip()
    instrumental = bool(req.get("instrumental"))
    vocal_mode = str(req.get("vocal_mode") or "auto").strip().lower()
    language = str(req.get("language") or "english").strip().lower()
    if language not in {"english", "chinese", "vietnamese"}:
        language = "english"
    language_name = {
        "english": "English",
        "chinese": "Simplified Chinese (Mandarin)",
        "vietnamese": "Vietnamese",
    }[language]
    duration = max(10, min(300, int(float(req.get("duration") or 180))))
    line_budget = max(12, min(56, int(duration / 5)))

    system = (
        "You are a professional songwriter and music producer preparing inputs for MiniMax Music 3. "
        "Return ONLY the four sentinel sections below, as plain UTF-8 text. Do NOT return JSON. "
        "The exact format is: <<<MM3_TITLE>>> then the title, <<<MM3_STYLE>>> then the style, "
        "<<<MM3_LYRICS>>> then the lyrics, and finally <<<MM3_END>>>. Put each marker on its own line. "
        "Never use those marker strings inside the title, style or lyrics themselves. "
        "The style field MUST be polished natural English even if the user writes in another language. "
        "Write the style as a MiniMax Music 3 Structured Caption with exactly these three headings in this order: "
        "### Global Metadata, ### Vocal Details, ### Arrangement. Use vivid English sentences, not a bare comma list. "
        "Global Metadata should cover genre, mood, rhythmic feel or BPM, and production profile. Vocal Details should "
        "state the selected vocal configuration, gender, register/timbre, delivery, harmony/backing-vocal rules and exclusions. "
        "Arrangement should cover main instruments, section development and production texture. "
        "Treat the UI vocal mode as higher priority than any conflicting gender wording in an existing style. "
        "Never silently reverse the requested vocal gender. Preserve other explicit user requirements. "
        "The UI-selected song language is a hard constraint for AI-created titles and lyrics. "
        "Keep the Music 3 style/structured caption itself in English. Do not mention that you translated anything. "
        "For lyrics, use standard English section markers such as [intro], [verse], [pre-chorus], [chorus], [bridge], [solo], [outro], even when lyrics are Chinese or Vietnamese. "
        "Do not use markdown fences or commentary outside the sentinel sections."
    )

    if instrumental:
        lyric_rule = (
            "This is INSTRUMENTAL. Leave the <<<MM3_LYRICS>>> section empty. The style must explicitly say instrumental with no vocals, "
            "identify the instrument or texture carrying the lead melody, and describe musical development across the requested duration."
        )
    elif lyrics:
        if language == "chinese":
            lyric_rule = (
                "The user already supplied lyrics. Convert every sung lyric line into natural Simplified Chinese / Mandarin while preserving section markers, meaning, emotion and singability. "
                "Do not leave English sung lines unless the user explicitly asked for bilingual lyrics. If an existing title is not Chinese, translate or recreate it as a concise Simplified Chinese title. "
                "Keep the production style in English."
            )
        elif language == "vietnamese":
            lyric_rule = (
                "The user already supplied lyrics. Keep or convert every sung lyric line into natural modern Vietnamese with correct Vietnamese diacritics, while preserving section markers, meaning, emotion and singability. "
                "Do not translate Vietnamese lyrics into Chinese or English unless the user explicitly asked for bilingual lyrics. If an existing title is not Vietnamese, translate or recreate it as a concise Vietnamese title. "
                "Keep the production style in English."
            )
        else:
            lyric_rule = (
                "The user already supplied lyrics. Convert every sung lyric line into natural English while preserving section markers, meaning, emotion and singability. "
                "Do not leave Chinese or Vietnamese sung lines unless the user explicitly asked for bilingual lyrics. If an existing title is not English, translate or recreate it as a concise English title. "
                "Keep the production style in English."
            )
    else:
        if language == "chinese":
            lyric_rule = (
                f"Write original singable lyrics in Simplified Chinese / Mandarin for about {duration} seconds "
                f"(roughly {line_budget} short lyric lines). Use natural modern Mandarin phrasing, concise rhythmic lines, "
                "and avoid mixing English into sung lines unless explicitly requested. Create the missing song title in Simplified Chinese too."
            )
        elif language == "vietnamese":
            lyric_rule = (
                f"Write original singable lyrics in natural modern Vietnamese for about {duration} seconds "
                f"(roughly {line_budget} short lyric lines). Use correct Vietnamese diacritics, concise rhythmic phrasing, strong vowel flow for singing, "
                "and avoid mixing Chinese or English into sung lines unless explicitly requested. Create the missing song title in Vietnamese too."
            )
        else:
            lyric_rule = (
                f"Write original singable lyrics in English for about {duration} seconds (roughly {line_budget} short lyric lines). "
                "Keep lines rhythmic, concise, natural, and easy to sing. Create the missing song title in English too."
            )

    user = "\n".join(
        [
            f"User AI instruction: {instruction or '(none — invent a tasteful, commercially usable concept)'}",
            f"Existing title: {title or '(missing — create one)'}",
            f"Existing style: {style or '(missing — create one in English)'}",
            f"Existing lyrics:\n{lyrics if lyrics else '(missing)'}",
            f"Target duration: {duration} seconds",
            f"Selected song language: {language_name}",
            f"Vocal mode: {vocal_mode}",
            _vocal_instruction(vocal_mode) if not instrumental else "No vocals.",
            lyric_rule,
            f"If a title is missing, create a concise memorable title in {language_name}. If a style is supplied, preserve its intent while translating/refining the style into English.",
        ]
    )

    data = _extract_song_fields(_chat(system, user))
    out_title = str(data.get("title") or title or "Untitled").strip().strip('"')[:120]
    out_style = str(data.get("style") or style or "").strip()
    out_lyrics = "" if instrumental else _clean_lyrics(str(data.get("lyrics") or lyrics or ""))
    if not instrumental:
        out_title, out_style, out_lyrics = _force_selected_language(out_title, out_style, out_lyrics, language, instruction)
        out_title = out_title[:120]
    if not out_style:
        raise RuntimeError("Translator model returned an empty music style. Try AI Fill again.")
    if not instrumental and not out_lyrics:
        raise RuntimeError("Translator model returned empty lyrics. Try AI Fill again.")
    return {"title": out_title or "Untitled", "style": out_style, "lyrics": out_lyrics}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = build_song_plan(payload)
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
        return 0
    except Exception as exc:
        sys.stderr.write(str(exc).strip() + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
