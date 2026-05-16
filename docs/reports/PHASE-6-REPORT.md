# Phase 6 Report — Chatbot + Embeddings

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 5–6

---

## Summary

Phase 6 built the RAG (Retrieval-Augmented Generation) mentor chatbot system: the code chunker, embedding pipeline, pgvector retriever, mentor bot orchestrator, and chat API endpoints. After Phase 6, participants can ask natural-language questions about their submitted code and receive answers grounded in their actual repository content.

---

## What Was Built

### Code Chunker
- **`backend/app/embedding/chunker.py`** — two chunking strategies:
  - `chunk_file(file_info, max_chunk_size=1500)` — sliding window chunker: 1,500-character chunks with 200-character overlap; each chunk carries `metadata` with `file_path`, `language`, `chunk_index`, `char_start`, `char_end`
  - `chunk_readme(readme_content, max_chunk_size=1500)` — splits by Markdown `#` headers to preserve semantic section boundaries; sections exceeding 1,500 characters are truncated; each chunk carries `metadata.section`
  - Both return chunk dicts with `chunk_type` ("code" or "readme") and `chunk_content`

### Embedder
- **`backend/app/embedding/embedder.py`** — `embed_repository(db, submission_id, files)`:
  - Processes up to 50 source files (sorted by line count descending to prioritize substantial files)
  - Generates up to 5 chunks per file (caps to avoid over-indexing large generated files)
  - Embeds each chunk via `OllamaProvider.embed()` with `nomic-embed-text` (768-dim output)
  - Inserts `RepoEmbedding` rows with `vector(768)` column, `chunk_type`, `chunk_content`, and `metadata`
  - Runs as a post-evaluation step in the ARQ task after scores are persisted (non-blocking: failure is logged but does not fail the evaluation)

### pgvector Retriever
- **`backend/app/embedding/retriever.py`** — `retrieve_similar_chunks(db, submission_id, query, top_k=5)`:
  - Embeds the user query via `OllamaProvider.embed()`
  - Executes cosine similarity search via raw SQL using the pgvector `<=>` operator: `WHERE submission_id = $1 ORDER BY embedding <=> $2::vector LIMIT $3`
  - Returns ranked list of chunk dicts with `id`, `chunk_type`, `content`, `metadata`, `similarity` score
  - Submission-scoped filter ensures chunks from other submissions are never returned

### Mentor Bot
- **`backend/app/chatbot/mentor.py`** — `MentorBot.respond(session, user_message)`:
  - Retrieves top-4 most similar chunks for the submission via the pgvector retriever
  - Fetches the evaluation report summary (final score, grade, top strengths, top weaknesses) from the database
  - Assembles a Jinja2 prompt with three context sections: evaluation summary, conversation history (last 10 messages), and retrieved code/README chunks
  - Calls `OllamaProvider.generate()` with `qwen2.5:7b` at temperature 0.4
  - Returns `(response_text, retrieved_chunks)` — the retrieved chunks are stored in `chat_messages.retrieved_chunks` JSONB for citation display in the UI
- **`backend/app/chatbot/context.py`** — `build_chat_history()` and `build_mentor_prompt()` helper functions

### Chat API
- **`backend/app/api/v1/chat.py`** — chat endpoints:
  - `POST /chat/sessions` — create a new `ChatSession` linked to a submission
  - `GET /chat/sessions/{id}` — get session metadata and message count
  - `POST /chat/sessions/{id}/messages` — send user message, trigger `MentorBot.respond()`, persist both user message and assistant response, return response with `retrieved_chunks`
  - `GET /chat/sessions/{id}/history` — full message history for display

---

## Key Decisions Made

- **50-file × 5-chunk limit** — embedding 250 vectors at ~50 ms per embed call takes approximately 12 seconds total; exceeding this would push evaluation time past demo tolerance. Files sorted by line count descending to prioritize substantial source files over small configs.
- **Cosine similarity via raw SQL** — SQLAlchemy does not natively support the pgvector `<=>` operator; raw SQL via `text()` was chosen over adding pgvector as a SQLAlchemy type extension to keep dependency surface minimal. The submission-scoped `WHERE` clause enables efficient filtered KNN search.
- **Chat history capped at 10 messages** for LLM context — with system prompt (~800 tokens), 4 retrieved chunks (~1,200 tokens), and 10 turns (~2,000 tokens), the total stays well within `qwen2.5:7b`'s context window. Longer histories are stored in the DB but not passed to the LLM.
- **Embedding runs post-evaluation** — embedding failures are non-fatal; a try/except in the ARQ task logs and continues. This ensures evaluation results are always persisted even if embedding (an Ollama call) times out.
- **Retrieved chunks stored per message** — `chat_messages.retrieved_chunks` JSONB stores the source citations for each assistant response, enabling the frontend to display "based on: `auth.py`, `models.py`" evidence cards without additional queries.

---

## Known Issues / Technical Debt

- **Streaming chat response not implemented** — the mentor response is returned as a full string after Ollama completes generation (10–30 seconds for longer responses). Token streaming via Ollama's `stream: true` API and SSE forwarding is planned for v1.1.
- **Embedding model fixed to `nomic-embed-text`** — if changed to a model producing different dimensions, all existing `repo_embeddings` rows become unusable (768-dim vectors cannot be compared to 1024-dim vectors). **Debt**: version the embedding model used per submission in `repo_embeddings.metadata`.
- **No chat session cleanup** — chat sessions are never deleted. Over time, the `chat_messages` table will grow unboundedly. **Debt**: add a TTL-based cleanup job (e.g., delete sessions older than 30 days).

---

## Verification Checklist

- [x] `chunk_file()` produces overlapping chunks with correct `char_start`/`char_end` metadata
- [x] `chunk_readme()` splits by `#` headers and truncates oversized sections
- [x] Embeddings stored with correct 768-dimensional vectors: `SELECT array_length(embedding::real[], 1) FROM repo_embeddings LIMIT 1` returns 768
- [x] Retriever returns top-4 results ranked by cosine similarity (closest first)
- [x] Retriever correctly scopes results to `submission_id` — cross-submission chunks not returned
- [x] `MentorBot.respond()` returns a non-empty response string when Ollama is running
- [x] Mentor response references code details from the retrieved chunks (tested with "how does authentication work?")
- [x] `chat_messages.retrieved_chunks` JSONB populated with correct chunk metadata
- [x] `POST /chat/sessions/{id}/messages` with no existing embeddings returns a graceful response (not an error)
