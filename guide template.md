# Guide Template — Usage Instructions (v2)

Save this file. Next time, just say: *"Use my guide template for [topic]"* and hand me this file (or paste it). I'll fill every section in for that topic, following the structure, depth, and rules below exactly.

---

## How to invoke it

```
Use my guide template for: <TOPIC>
Audience: senior engineer already familiar with the basics
Scope note (optional): <anything specific to include/exclude, e.g.
  "focus on the async path" or "skip the provider comparison table">
Tooling note (optional): <if the topic has an ecosystem of competing tools,
  say whether you want one opinionated stack, or every real fork explained
  with both sides shown — default is the latter: explain forks, don't force
  a single stack unless you ask for a recommendation>
```

If no scope note is given, I default to the same breadth as the earlier guides: comprehensive, cookbook-depth, senior-to-senior, with every genuine tool/approach fork explained rather than silently picked for you.

---

# THE TEMPLATE

## Non-negotiable rules (apply to every guide built from this template)

1. **Not an introduction.** Assume the reader already knows the tool's public API / basic usage. Never explain what the tool is for at a beginner level. Open with a one-paragraph blockquote that states the guide's scope, the assumed audience, and — if versions matter — the date/version it's current as of.
2. **Every diagram is Mermaid code**, fenced with ` ```mermaid `. No ASCII art, no box-drawing characters. Use `sequenceDiagram` for request/response or multi-actor flows, `flowchart` (TD or LR) for architecture/data-flow/decision trees, and `classDiagram`/`erDiagram` only when the topic is genuinely structural (data models, class hierarchies).
3. **"Why," not just "how."** Every mechanism described must be tied to the design reasoning behind it — what problem it solves, what the alternative would cost. A section that only says *what* a feature does without saying *why* it's built that way is incomplete.
4. **Precision over padding, but don't undershoot depth.** Dense, cookbook-style writing — but "dense" means information-per-sentence, not short overall. Every core mechanism gets full treatment: the mechanism itself, why it exists, at least one concrete code example, the failure mode if misunderstood, and — where relevant — how it changes under scale/production conditions. Tables for anything comparative (options, tradeoffs, error causes/fixes). Code blocks only where they illustrate a real mechanism, not filler boilerplate. When in doubt about whether a sub-topic deserves its own paragraph or subsection, err toward including it — the guide should be usable as the only reference someone needs, with external links (rule 8) as the escape hatch for genuine depth beyond scope, not as a substitute for adequate coverage.
5. **Every genuine tool/approach fork gets both sides, not a silent pick.** If the topic has more than one legitimate way to do something (competing libraries, competing patterns, a stable-vs-emerging approach), explain *why* the fork exists, show working code for each side, and give a concrete "choose X when..., choose Y when..." table. Never silently default to one option and omit the other, and never present a genuine platform requirement (something with no real alternative) as if it were a stylistic choice — distinguish "this is how the platform works" from "this is a decision you get to make," explicitly, the way a senior engineer would when onboarding a peer.
6. **Currency check.** If the topic involves packages, versions, APIs, or anything that changes over time, verify current versions/behavior via search before writing — state what was checked and when, and flag anything not fully confirmable (e.g., "not yet officially certified against X, but no reported issues") rather than asserting confidently. If a real, dated incident is relevant (a security disclosure, a breaking migration, a supply-chain event), name it with its actual date rather than gesturing at "known issues."
7. **End with an anti-patterns section, a cheat sheet, and a references section.** No guide is complete without naming the mistakes a practitioner will actually make, a compressed scannable summary, and a curated set of primary sources so the reader can self-study past what the guide covers. The references section is non-negotiable on every guide, not an optional nicety.
8. **File, not chat.** These are long-form reference documents — always delivered as a markdown file, never inlined into the conversation.

---

## Structure

Adapt section *count* and *naming* to the topic — not every guide needs all 20 sections a Django-scale guide needed. But the **shape** below is fixed: concepts → decision/orientation → mechanism/architecture → practical application → production concerns → security → testing → troubleshooting → anti-patterns → cheat sheet → references. Skipping a category because the topic doesn't need it is fine; skipping it because it's harder to write is not.

### 1. Title + Positioning Blockquote
- One line title.
- Blockquote: what this guide is (and isn't), assumed audience, currency date/version if relevant, and — if applicable — a one-line flag of any real dated incident (security/supply-chain/breaking-change) worth knowing up front.

### 2. Table of Contents
- Numbered, linked to anchors. Mirrors the actual section list below.

### 3. Concepts — How It Actually Works
- The mental model a practitioner needs before anything else makes sense.
- **Include a Mermaid diagram here** if the topic has any flow, sequence, or multi-component interaction (it almost always does).
- A vocabulary table if the topic has terms of art that get used loosely/incorrectly elsewhere.
- Go deep enough that a reader could explain the mechanism to someone else afterward, not just recognize the term.

### 4. Decision / Orientation Section
- "Which approach do I need" — a comparison table of the topic's major forks (e.g., which package, which pattern, which flow) mapped to when each is the right call. Every guide needs the reader to be able to place themselves before diving into implementation.
- Explicitly separate genuine choices (competing tools/patterns) from platform requirements (things with no real alternative) — don't let the two get flattened into one table as if both were equally optional.

### 5+. Core Implementation Sections (as many as the topic needs)
- Installation / setup (with a **verified current-version table**: package, version, compatibility notes, last-checked date).
- Configuration reference (settings, with inline comments explaining *why* each non-default value is set, not just what it does).
- The core mechanism(s) — broken into logical sub-sections, each covering one coherent piece end-to-end (not "part 1 of the same feature split arbitrarily").
- Wherever the topic has layered behavior (e.g., scopes at endpoint-level vs. object-level; middleware vs. decorators vs. signals), make the **layers explicit** and show what each layer can't do that the next layer up handles.
- Wherever the topic has a genuine tool/approach fork (rule 5), show both sides in full working code, not a snippet for the recommended one and a mention of the alternative.
- Extension points — where and how a senior practitioner is meant to override/customize, not just use defaults.

### N. Scaling / Production Section
- What changes between "works on my machine" and production load.
- Concrete, mechanism-level advice (not "cache it" — *what* to cache, *why*, and the failure mode if you don't).

### N+1. Security Checklist
- A literal checklist (`- [ ]`), specific to the topic, not generic advice.
- Include any real, dated, verified incident relevant to the topic's ecosystem, with what to actually check/do about it — not a vague "stay updated."

### N+2. Testing
- How to test this topic's specific mechanisms, including the non-obvious gotchas (things that silently don't work in a naive test setup).

### N+3. Common Errors & Fixes
- Table: Error | Root Cause | Fix. Real error strings/messages where possible, not paraphrased.

### N+4. Anti-Patterns
- Named, recognizable mistakes a practitioner at this level will actually make — not generic "don't write bad code" advice. Each one should make an experienced reader wince in recognition.

### N+5. Quick Reference / Mental Model Cheat Sheet
- Compressed, scannable. Code blocks for the "always set these explicitly" settings/commands. A final condensed version of the core mental model in a few lines — the thing the reader should be able to recall without looking anything up.

### N+6. References & Further Reading {#references}
- Always present, always last. A curated, categorized list of primary sources so the reader can self-study beyond the guide, not a generic "see the docs" line.
- Categorize into: **Official docs/specs** (the canonical source for the topic), **Source code worth reading** (the actual implementation, or a key RFC/design doc, when reading the source clarifies the mechanism better than prose can), **Deep dives** (long-form articles, talks, or papers that go further than this guide's scope on a specific sub-topic), and **Community/ecosystem** (where practitioners discuss current issues — a Discord, a working group, a changelog feed) — omit any category that doesn't apply rather than padding it.
- Every link should have a one-line note on *why* it's worth the reader's time, not just a bare URL — a reference list without annotation is a link dump, not a self-study path.
- Prefer primary/official sources over aggregator blog posts; if a specific third-party article was unusually good for a sub-topic (e.g., the definitive deep-dive on a particular mechanism), it's fine to include it, annotated as such.

---

## Formatting conventions to reuse exactly

- `#`/`##` headers with `{#anchor}` tags matching the TOC.
- Tables for anything with more than 2 comparable dimensions.
- ` ```mermaid ` for every diagram, ` ```python `/` ```bash ` etc. for code, matched to the actual language.
- Bold used sparingly, only for the one key insight in a paragraph — not decoratively.
- Section dividers (`---`) between major numbered sections.
- References formatted as a bulleted list per category, `[Title](URL) — one-line note on why it matters`.
- No emoji, no marketing language, no "Great question!" framing — direct, technical register throughout, as if written by one senior engineer for another.

---

## Example section skeleton (copy this shape for each new numbered section)

```markdown
## N. [Section Name] {#anchor}

[One or two sentences: what this section covers and why it matters —
what breaks or gets misunderstood without this knowledge.]

[Mermaid diagram if the section describes a flow/architecture]

[Core explanation, mechanism-first: what actually happens, in the order
it happens, tied back to *why* it's built that way. If this section
involves a genuine tool/approach fork, show both sides in full, with a
table of when each is the right call.]

[Code example — only if it demonstrates the actual mechanism, not
generic setup. Show both sides of a fork here if applicable.]

**[One bolded key insight or gotcha most people miss.]**
```

## Example references section shape

```markdown
## N+6. References & Further Reading {#references}

**Official docs/specs**
- [Title](URL) — why this is the canonical source for X.

**Source code worth reading**
- [Title](URL) — reading the actual implementation of Y clarifies Z better than any prose explanation.

**Deep dives**
- [Title](URL) — goes further than this guide on the specific sub-topic of W.

**Community/ecosystem**
- [Title](URL) — where current issues/discussions for this topic actually happen.
```

---

*End of template. To use: reply with "use my guide template for X" and any scope/tooling notes — I'll produce the full guide as a markdown file, matching this structure exactly, always ending with an annotated references section.*
