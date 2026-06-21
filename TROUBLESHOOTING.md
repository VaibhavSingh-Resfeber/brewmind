# Troubleshooting Log

Real bugs encountered while building BrewMind's vector search pipeline — kept here for future reference and as honest documentation of the debugging process.

---

## Issue 1 — `psycopg2.ProgrammingError: can't adapt type 'dict'`

**When it happened:** Running `scripts/seed_db.py` for the first time. All 7 cafes failed with the same error.

**Symptom:**
```
psycopg2.ProgrammingError: can't adapt type 'dict'
```

**Root cause:**
`cafes_seed.json` stores quality metadata alongside each value:
```json
"bean_origin_style": {
    "value": "single origin, rotating, own roastery",
    "confidence": "high",
    "evidence": "Roasts on site..."
}
```

`vector_store.py` was passing the entire nested object to PostgreSQL:
```python
"bean_origin_style": cafe_data.get("bean_origin_style")
```

PostgreSQL's `text` column has no idea how to store a Python dict.

**Fix:**
Extract only the `.value` field, with a safe fallback if the field is missing:
```python
"bean_origin_style": cafe_data["bean_origin_style"]["value"] 
                     if cafe_data.get("bean_origin_style") 
                     else None
```

**Lesson:**
When source data has nested structure for data-quality reasons (confidence, evidence), the storage layer must explicitly unwrap to the field the database column actually expects. Don't assume `.get()` returns a flat value — check the JSON shape first.

---

## Issue 2 — `psycopg2.errors.SyntaxError: syntax error at or near ":"`

**When it happened:** First attempt at `search_cafes()` — running a semantic search query.

**Symptom:**
```sql
LINE 7:    1 - (embedding <=> :embedding::vector) AS similarity
                              ^
syntax error at or near ":"
```

**Root cause:**
SQLAlchemy's named parameter syntax (`:embedding`) and PostgreSQL's type-cast syntax (`::vector`) both use colons. Written together as `:embedding::vector`, SQLAlchemy's parser greedily consumed `:embedding:` as the parameter name — including the second colon — then choked on the remainder.

**Fix (intermediate):**
Add a space to separate the named parameter from the cast:
```sql
:embedding ::vector
```

**Lesson:**
When mixing ORM-level named parameters with database-specific syntax that also uses `:` or `::`, the parser can't always disambiguate. A single space changed the tokenization entirely. (This fix was later superseded by Issue 3's solution — see below.)

---

## Issue 3 — `search_cafes()` returns 0 or fewer rows than `limit`

**When it happened:** After fixing Issue 2, searches ran without errors but returned wrong results:
- `limit=3` sometimes returned only 1 row
- Some queries returned 0 rows with no error at all

**Symptom:**
```python
search_cafes(db, "good for working laptop wifi", limit=3)
# → []  (empty, no exception raised)
```

**Debugging process:**
1. Confirmed all 7 rows exist in `cafes` table (`SELECT COUNT(*)` → 7) ✅
2. Confirmed embeddings are stored as real vectors, not strings ✅
3. Tested the same SQL **without** `ORDER BY` → 3 rows returned ✅
4. Tested the same SQL **with** `ORDER BY` → 0 rows, no error ❌

**Root cause:**
The cosine-distance expression `embedding <=> '<8000-char vector string>' ::vector` was repeated identically in both `SELECT` and `ORDER BY`. With a very long string literal repeated twice in one query, psycopg2/PostgreSQL silently failed to execute correctly — no exception, just an empty result set.

Separately, passing `limit` as a named parameter (`:limit`) was also unreliable, since `LIMIT` is a reserved SQL keyword and conflicted with SQLAlchemy's parameter binding in this context.

**Fix:**
1. Inject `limit` directly as a Python int via f-string (safe — `int()` can never contain SQL):
   ```python
   LIMIT {int(limit)}
   ```
2. Restructure the query using a CTE (`WITH ... AS`) so the expensive vector expression is computed **once**, given an alias (`similarity`), and the outer query orders by that alias instead of repeating the expression:
   ```sql
   WITH similarities AS (
       SELECT ..., 1 - (embedding <=> '<vec>' ::vector) AS similarity
       FROM cafes
   )
   SELECT * FROM similarities
   ORDER BY similarity DESC
   LIMIT {int(limit)}
   ```

**Lesson:**
Repeating a large/complex expression in both `SELECT` and `ORDER BY` can fail silently rather than erroring — making it look like a data problem when it's a query-structure problem. CTEs (`WITH` clauses) are the right tool whenever a computed value is needed in multiple places in a query: compute once, name it, reference the name.

---

## Issue 4 (architectural, not a bug) — Structured facts vs. semantic search

**When it happened:** After fixing Issue 3, searches worked correctly but results for `"good for working laptop wifi"` didn't surface ALRIGHTY (which has `wifi: true, good_for_working: true`) with a strong score.

**Why this isn't a bug:**
The embedding only encodes what's written in `embed_text`. ALRIGHTY's `embed_text` describes its industrial roastery and sustainability mission — it never uses words like "wifi" or "laptop". Cosine similarity correctly found no semantic overlap, because there genuinely isn't any in the text.

**Decision:**
Rather than rewriting `embed_text` to stuff in keywords (a band-aid), the correct fix is **hybrid search**:
- Structured boolean fields (`wifi`, `good_for_working`) should be used as **filters**
- Embeddings should be reserved for **fuzzy/subjective concepts** ("quiet", "serious", "third-wave")
- Translating natural-language queries ("a place I can be productive") into structured filters requires an LLM query-understanding step — planned for Week 3 (Claude integration)

**Lesson:**
Not every imperfect result is a bug to patch at the data layer. Sometimes it's a signal that two different retrieval strategies (structured filtering vs. semantic search) need to be combined — and that the right place to bridge natural language → structured filters is an LLM, not the embedding model.

---

## Summary table

| # | Issue | Layer | Fix type |
|---|-------|-------|----------|
| 1 | `can't adapt type 'dict'` | Data mapping | Extract nested `.value` field |
| 2 | `syntax error at ":"` | SQL syntax | Add space between `:param` and `::cast` |
| 3 | Wrong row count / 0 rows | Query structure | CTE to avoid repeated vector expression |
| 4 | Weak match for structured queries | Architecture | Defer to hybrid search (Week 3) |
