# Guide Template — Usage Instructions

Save this file. Next time, just say: *"Use my guide template for [topic]"* and hand me this file (or paste it). I'll fill every section in for that topic, following the structure, depth, and rules below exactly.

---

## How to invoke it

```
Use my guide template for: <TOPIC>
Audience: senior engineer already familiar with the basics
Scope note (optional): <anything specific to include/exclude, e.g.
  "focus on the async path" or "skip the provider comparison table">
```

If no scope note is given, I default to the same breadth as the earlier guides: comprehensive, cookbook-depth, senior-to-senior.

---

# THE TEMPLATE

## Non-negotiable rules (apply to every guide built from this template)

1. **Not an introduction.** Assume the reader already knows the tool's public API / basic usage. Never explain what the tool is for at a beginner level. Open with a one-paragraph blockquote that states the guide's scope, the assumed audience, and — if versions matter — the date/version it's current as of.
2. **Every diagram is Mermaid code**, fenced with ` ```mermaid `. No ASCII art, no box-drawing characters. Use `sequenceDiagram` for request/response or multi-actor flows, `flowchart` (TD or LR) for architecture/data-flow/decision trees, and `classDiagram`/`erDiagram` only when the topic is genuinely structural (data models, class hierarchies).
3. **"Why," not just "how."** Every mechanism described must be tied to the design reasoning behind it — what problem it solves, what the alternative would cost. A section that only says *what* a feature does without saying *why* it's built that way is incomplete.
4. **Precision over padding.** Dense, cookbook-style writing. Tables for anything comparative (options, tradeoffs, error causes/fixes). Code blocks only where they illustrate a real mechanism, not filler boilerplate.
5. **Currency check.** If the topic involves packages, versions, APIs, or anything that changes over time, verify current versions/behavior via search before writing — state what was checked and when, and flag anything not fully confirmable (e.g., "not yet officially certified against X, but no reported issues") rather than asserting confidently.
6. **End with a anti-patterns section and a cheat sheet.** No guide is complete without naming the mistakes a practitioner will actually make, and without a compressed, scannable summary at the end.
7. **File, not chat.** These are long-form reference documents — always delivered as a markdown file, never inlined into the conversation.

---

## Structure

Adapt section *count* and *naming* to the topic — not every guide needs all 20 sections a Django-scale guide needed. But the **shape** below is fixed: concepts → mechanism/architecture → practical application → production concerns → security → testing → troubleshooting → anti-patterns → cheat sheet. Skipping a category because the topic doesn't need it is fine; skipping it because it's harder to write is not.

### 1. Title + Positioning Blockquote
- One line title.
- Blockquote: what this guide is (and isn't), assumed audience, currency date/version if relevant.

### 2. Table of Contents
- Numbered, linked to anchors. Mirrors the actual section list below.

### 3. Concepts — How It Actually Works
- The mental model a practitioner needs before anything else makes sense.
- **Include a Mermaid diagram here** if the topic has any flow, sequence, or multi-component interaction (it almost always does).
- A vocabulary table if the topic has terms of art that get used loosely/incorrectly elsewhere.

### 4. Decision / Orientation Section
- "Which approach do I need" — a comparison table of the topic's major forks (e.g., which package, which pattern, which flow) mapped to when each is the right call. Every guide needs the reader to be able to place themselves before diving into implementation.

### 5+. Core Implementation Sections (as many as the topic needs)
- Installation / setup (with a **verified current-version table**: package, version, compatibility notes, last-checked date).
- Configuration reference (settings, with inline comments explaining *why* each non-default value is set, not just what it does).
- The core mechanism(s) — broken into logical sub-sections, each covering one coherent piece end-to-end (not "part 1 of the same feature split arbitrarily").
- Wherever the topic has layered behavior (e.g., scopes at endpoint-level vs. object-level; middleware vs. decorators vs. signals), make the **layers explicit** and show what each layer can't do that the next layer up handles.
- Extension points — where and how a senior practitioner is meant to override/customize, not just use defaults.

### N. Scaling / Production Section
- What changes between "works on my machine" and production load.
- Concrete, mechanism-level advice (not "cache it" — *what* to cache, *why*, and the failure mode if you don't).

### N+1. Security Checklist
- A literal checklist (`- [ ]`), specific to the topic, not generic advice.

### N+2. Testing
- How to test this topic's specific mechanisms, including the non-obvious gotchas (things that silently don't work in a naive test setup).

### N+3. Common Errors & Fixes
- Table: Error | Root Cause | Fix. Real error strings/messages where possible, not paraphrased.

### N+4. Anti-Patterns
- Named, recognizable mistakes a practitioner at this level will actually make — not generic "don't write bad code" advice. Each one should make an experienced reader wince in recognition.

### N+5. Quick Reference / Mental Model Cheat Sheet
- Compressed, scannable. Code blocks for the "always set these explicitly" settings/commands. A final condensed version of the core mental model in a few lines — the thing the reader should be able to recall without looking anything up.

---

## Formatting conventions to reuse exactly

- `#`/`##` headers with `{#anchor}` tags matching the TOC.
- Tables for anything with more than 2 comparable dimensions.
- ` ```mermaid ` for every diagram, ` ```python `/` ```bash ` etc. for code, matched to the actual language.
- Bold used sparingly, only for the one key insight in a paragraph — not decoratively.
- Section dividers (`---`) between major numbered sections.
- No emoji, no marketing language, no "Great question!" framing — direct, technical register throughout, as if written by one senior engineer for another.

---

## Example section skeleton (copy this shape for each new numbered section)

```markdown
## N. [Section Name] {#anchor}

[One or two sentences: what this section covers and why it matters —
what breaks or gets misunderstood without this knowledge.]

[Mermaid diagram if the section describes a flow/architecture]

[Core explanation, mechanism-first: what actually happens, in the order
it happens, tied back to *why* it's built that way.]

[Code example — only if it demonstrates the actual mechanism, not
generic setup]

**[One bolded key insight or gotcha most people miss.]**
```

---

*End of template. To use: reply with "use my guide template for X" and any scope notes — I'll produce the full guide as a markdown file, matching this structure exactly.*
