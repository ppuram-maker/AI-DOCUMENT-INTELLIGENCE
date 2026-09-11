def chunk_text(text: str, max_chars: int = 8000) -> list[str]:
    """
    Split document text into chunks of approximately max_chars characters.

    - Prefers splitting at paragraph boundaries ("\\n\\n") when possible.
    - If a paragraph exceeds max_chars, it is split further into smaller pieces.
    - Preserves all original text without silently dropping content.
    - Returns an empty list for empty or whitespace-only input.

    Args:
        text (str): The document text to be split into chunks.
        max_chars (int): The target maximum number of characters per chunk.

    Returns:
        list[str]: A list of text chunks.
    """
    # 1. Handle empty or whitespace-only input
    if not text or not text.strip():
        return []

    if max_chars <= 0:
        raise ValueError("max_chars must be a positive integer.")

    # Helper function to break down paragraphs that exceed max_chars
    def split_large_paragraph(paragraph: str) -> list[str]:
        # If the paragraph contains single newlines, try splitting on them first
        if "\n" in paragraph:
            lines = paragraph.split("\n")
            sub_chunks = []
            current_lines = []
            current_len = 0

            for line in lines:
                # If a single line itself is longer than max_chars, slice it by character count
                if len(line) > max_chars:
                    if current_lines:
                        sub_chunks.append("\n".join(current_lines))
                        current_lines = []
                        current_len = 0
                    for i in range(0, len(line), max_chars):
                        sub_chunks.append(line[i : i + max_chars])
                else:
                    # Calculate length if we add this line (+1 for the newline separator)
                    line_cost = len(line) + (1 if current_lines else 0)
                    if current_len + line_cost > max_chars:
                        sub_chunks.append("\n".join(current_lines))
                        current_lines = [line]
                        current_len = len(line)
                    else:
                        current_lines.append(line)
                        current_len += line_cost

            if current_lines:
                sub_chunks.append("\n".join(current_lines))
            return sub_chunks

        # If there are no newlines, split directly by character slices
        return [
            paragraph[i : i + max_chars]
            for i in range(0, len(paragraph), max_chars)
        ]

    # 2. Split text at paragraph boundaries ("\n\n")
    raw_paragraphs = text.split("\n\n")

    # 3. Ensure every paragraph is within max_chars by splitting any oversized ones
    paragraphs = []
    for p in raw_paragraphs:
        if len(p) > max_chars:
            paragraphs.extend(split_large_paragraph(p))
        else:
            paragraphs.append(p)

    # 4. Group paragraphs into chunks up to max_chars
    chunks = []
    current_chunk = []
    current_length = 0

    for p in paragraphs:
        # Cost of joining with "\n\n" if there are already paragraphs in current_chunk
        separator_len = 2 if current_chunk else 0

        if current_length + len(p) + separator_len <= max_chars:
            current_chunk.append(p)
            current_length += len(p) + separator_len
        else:
            # Current chunk is full, save it and start a new chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_length = len(p)

    # Append any remaining paragraphs
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
