# Graph Report - .  (2026-07-02)

## Corpus Check
- 9 files · ~33,508 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 593 nodes · 1695 edges · 16 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]

## God Nodes (most connected - your core abstractions)
1. `t()` - 38 edges
2. `z()` - 34 edges
3. `Ed` - 34 edges
4. `r()` - 33 edges
5. `o()` - 30 edges
6. `fd` - 30 edges
7. `M()` - 29 edges
8. `od()` - 27 edges
9. `md()` - 26 edges
10. `fo` - 24 edges

## Surprising Connections (you probably didn't know these)
- `BLUE and ROUGE scores are heavily rely on surface-level lexical overlaps, often` --uses--> `LLMProvider`  [INFERRED]
  evaluation/eval_flowise.py → evaluation/llm_provider.py
- `Zero-RAG baseline evaluation.  Identical metrics to ``eval_flowise.py`` (ROUGE,` --uses--> `LLMProvider`  [INFERRED]
  evaluation/zeroRAG.py → evaluation/llm_provider.py
- `Query the model directly (no retrieval). Returns {"text": ...} or {"error": ...}` --uses--> `LLMProvider`  [INFERRED]
  evaluation/zeroRAG.py → evaluation/llm_provider.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (109): A(), aa(), Ae(), Ag(), an(), Ao, at(), B() (+101 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (24): Ad(), as, bd(), cs, dd(), ds, es, fd (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (92): _(), ai(), ar(), ba(), bl(), bm(), br(), ca() (+84 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (9): Ed, id(), Nd(), od(), ts, Tt(), Wd, wm() (+1 more)

### Community 4 - "Community 4"
Cohesion: 0.1
Nodes (6): fo, Je(), Ne(), oe(), Po, Ye()

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (5): al(), co, Mo, o(), To

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (20): compute_bertscore(), compute_bleu(), compute_rouge(), _get_bert_scorer(), llm_judge(), load_dataset(), query(), BLUE and ROUGE scores are heavily rely on surface-level lexical overlaps, often (+12 more)

### Community 7 - "Community 7"
Cohesion: 0.1
Nodes (4): ns(), Qd, vs, Zd()

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (2): be(), Qr

### Community 9 - "Community 9"
Cohesion: 0.22
Nodes (3): gs, Jd, Yd()

### Community 10 - "Community 10"
Cohesion: 0.29
Nodes (1): ld

### Community 11 - "Community 11"
Cohesion: 0.57
Nodes (6): analyze(), compare(), load(), main(), out(), Statistical analysis of German and English evaluation datasets.

### Community 12 - "Community 12"
Cohesion: 0.6
Nodes (5): compute_bleu(), compute_rouge(), llm_judge(), load_dataset(), run_evaluation()

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **1 isolated node(s):** `Statistical analysis of German and English evaluation datasets.`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (2 nodes): `main()`, `main.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (2 nodes): `test.py`, `query()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `soofi-model.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Ed` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`, `Community 8`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `fd` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `od()` connect `Community 3` to `Community 0`, `Community 1`, `Community 9`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **What connects `Statistical analysis of German and English evaluation datasets.` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.04 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.03 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._