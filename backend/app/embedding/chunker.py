from typing import List, Dict, Any

DEFAULT_MAX_CHUNK_SIZE = 1500
OVERLAP_CHARS = 200


def chunk_file(
    file_info: Dict[str, Any],
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
) -> List[Dict[str, Any]]:
    """Split a source-code file into overlapping fixed-size chunks.

    Args:
        file_info: A file dict as produced by ``collect_files``, containing at
                   minimum ``content``, ``path``, and optionally ``language``.
        max_chunk_size: Maximum number of characters per chunk (default 1500).

    Returns:
        A list of chunk dicts, each with:
            chunk_type    : "code"
            chunk_content : the text slice
            metadata      : {file_path, language, chunk_index, char_start, char_end}
    """
    content: str = file_info.get("content", "")
    path: str = file_info.get("path", "unknown")
    language: str = file_info.get("language", "Unknown")

    if not content:
        return []

    chunks: List[Dict[str, Any]] = []
    start = 0
    chunk_idx = 0

    while start < len(content):
        end = min(start + max_chunk_size, len(content))
        chunk_text = content[start:end]

        chunks.append({
            "chunk_type": "code",
            "chunk_content": chunk_text,
            "metadata": {
                "file_path": path,
                "language": language,
                "chunk_index": chunk_idx,
                "char_start": start,
                "char_end": end,
            },
        })

        chunk_idx += 1
        if end == len(content):
            break
        # Overlap: step back by OVERLAP_CHARS so consecutive chunks share context
        start = end - OVERLAP_CHARS

    return chunks


def chunk_readme(
    readme_content: str,
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
) -> List[Dict[str, Any]]:
    """Split a README into semantic chunks delimited by Markdown section headers.

    Each ``#``-prefixed heading starts a new chunk.  Sections longer than
    ``max_chunk_size`` characters are truncated to keep embedding quality high.

    Args:
        readme_content: The raw README text.
        max_chunk_size: Maximum characters per chunk (default 1500).

    Returns:
        A list of chunk dicts, each with:
            chunk_type    : "readme"
            chunk_content : "# <header>\\n<body>"
            metadata      : {section}
    """
    if not readme_content:
        return []

    sections: List[Dict[str, str]] = []
    current_header = "intro"
    current_lines: List[str] = []

    for line in readme_content.split("\n"):
        if line.startswith("#"):
            # Flush the previous section
            if current_lines:
                sections.append({
                    "header": current_header,
                    "content": "\n".join(current_lines),
                })
            current_header = line.lstrip("#").strip() or "section"
            current_lines = []
        else:
            current_lines.append(line)

    # Flush the final section
    if current_lines:
        sections.append({
            "header": current_header,
            "content": "\n".join(current_lines),
        })

    chunks: List[Dict[str, Any]] = []
    for section in sections:
        body = section["content"].strip()
        if not body:
            continue
        chunk_text = f"# {section['header']}\n{body}"
        # Truncate oversized sections
        chunk_text = chunk_text[:max_chunk_size]
        chunks.append({
            "chunk_type": "readme",
            "chunk_content": chunk_text,
            "metadata": {"section": section["header"]},
        })

    return chunks
