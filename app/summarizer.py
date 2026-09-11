import os
from google import genai

from app.chunker import chunk_text


def summarize_text(text: str) -> str:
    """
    Summarize the provided document text using Google Gemini Interactions API.

    Handles both short and long documents:
    - If the document fits in a single chunk, it is summarized directly.
    - If the document spans multiple chunks, a Map-Reduce approach is used:
      1. Each chunk is summarized separately to capture all details.
      2. The chunk summaries are combined.
      3. A final pass generates one unified document summary.
    """
    # 1. Validate API key from environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set the GEMINI_API_KEY environment variable."
        )

    # 2. Validate non-empty document text
    if not text or not text.strip():
        raise ValueError("Cannot summarize empty text.")

    # 3. Initialize the Gemini client using the environment variable
    client = genai.Client(api_key=api_key)

    # Helper function to call the Gemini Interactions API cleanly with error handling
    def call_gemini(prompt: str) -> str:
        try:
            interaction = client.interactions.create(
                model="gemini-3.6-flash",
                input=prompt,
            )
            return interaction.output_text or ""
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}") from e

    # 4. Chunk the document text into manageable pieces (~8000 characters).
    # WHY CHUNKING IS NEEDED:
    # Large documents can exceed context limits or cause the model to overlook
    # finer details in the middle of long text. Splitting the document ensures
    # that all paragraphs and facts are thoroughly evaluated without dropping content.
    chunks = chunk_text(text, max_chars=8000)

    if not chunks:
        raise ValueError("Cannot summarize empty text.")

    # 5. If there is only one chunk, summarize it directly in a single call
    if len(chunks) == 1:
        prompt = (
            "You are an AI document assistant. Please provide a clear and concise summary "
            "of the following document text, preserving all important facts, key findings, "
            f"and core details:\n\n{chunks[0]}"
        )
        return call_gemini(prompt)

    # 6. MULTI-CHUNK SUMMARIZATION (MAP-REDUCE PATTERN):
    #
    # Step A (Map): Summarize each chunk individually.
    # Each section is summarized separately so every portion of the document
    # contributes its important facts without anything being silently lost.
    chunk_summaries = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_prompt = (
            f"You are an AI document assistant. Summarize section {index} of {len(chunks)} "
            "from a larger document. Preserve all key facts, numbers, names, and critical points:\n\n"
            f"{chunk}"
        )
        summary = call_gemini(chunk_prompt)
        chunk_summaries.append(summary)

    # Step B: Combine all individual chunk summaries
    combined_summaries = "\n\n".join(chunk_summaries)

    # Step C (Reduce): Generate the final overall summary.
    # The intermediate summaries are synthesized into a single, cohesive,
    # and easy-to-read final summary for the entire document.
    final_prompt = (
        "You are an AI document assistant. Below are section summaries from a multi-part document. "
        "Synthesize them into one comprehensive, unified, and well-structured overall summary, "
        f"preserving all key facts, conclusions, and important insights:\n\n{combined_summaries}"
    )

    return call_gemini(final_prompt)
