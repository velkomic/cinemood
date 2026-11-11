# Models and API budget

Source check: 2026-11-09. Research recommendation only; model choices and spending allocation are not yet accepted. Documentation review only: no keys inspected, paid API calls made, or account access verified.

## Recommended starting point

| Role | Proposed model/configuration | Published standard USD price per 1M tokens |
| --- | --- | --- |
| Catalog and query embeddings | `text-embedding-3-small`, default 1,536 dimensions | $0.02 input |
| Constraint extraction and short explanations | `gpt-5.4-mini-2026-03-17`, reasoning effort `none` | $0.75 input; $4.50 output; $0.075 cached input |

Embedding price comes from the [OpenAI model page](https://developers.openai.com/api/docs/models/text-embedding-3-small); default dimensions and the optional `dimensions` parameter come from the [embeddings guide](https://developers.openai.com/api/docs/guides/embeddings). Keep 1,536 dimensions initially and use the same model/configuration for ingestion and queries; changing them would require rebuilding compatible stored vectors.

The [GPT-5.4 mini page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) verifies these prices, the dated snapshot, Chat Completions/Responses support, structured outputs, streaming, and `none` reasoning effort. This is a pragmatic starting candidate for the small MVP, pending the agreed human-reviewed evaluation. It is not a claim that quality or latency has been measured. The page lists no free-tier support and a 10% uplift for regional data-residency endpoints; this estimate assumes the ordinary endpoint.

Older economical models have near-term retirement dates: GPT-4o mini and GPT-4.1 mini on 2027-01-14, GPT-5 mini on 2026-12-11, and GPT-5.4 nano on 2027-04-01. Prefer the established March 2026 mini snapshot for a new implementation rather than plan an immediate migration. Recheck lifecycle before implementation. [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)

## LangChain flow and limits

Use `langchain-openai`: `OpenAIEmbeddings` for ingestion/query vectors and `ChatOpenAI` for two explicit model calls. LangChain documents embedding methods and configurable dimensions in its [OpenAIEmbeddings integration](https://docs.langchain.com/oss/python/integrations/embeddings/openai), and individual structured calls with `with_structured_output(..., method="json_schema")`, token streaming, and `stream_usage=True` in its [ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai). No agent or LangGraph orchestration is required for this proposed sequence.

1. Extract and validate the supported constraints into a Pydantic schema.
2. Embed the semantic request, apply validated database filters, and retrieve candidates.
3. Stream short explanations grounded in the retrieved records; render movie facts from the database.

Strict structured output supports a JSON Schema subset: use required fields with nullable values for absent constraints, and forbid extra properties. Handle refusals and incomplete responses separately. Schema compliance does not establish whether an extracted constraint is correct; application validation and evaluation remain necessary. [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

The sequential extraction call adds latency before retrieval and explanation streaming can begin. Streaming improves visible progress after generation starts; it does not remove that delay. Measure extraction duration, time to first explanation text, and total completion time during verification. Preserve retrieved cards if explanation generation fails, as required by the project scope.

## Illustrative experiment budget

Assumptions: 1,000 movies averaging 300 embedding tokens each; 200 recommendation requests; each request embeds 50 tokens and makes two chat calls. Extraction uses 600 input/100 output tokens; explanation uses 1,400 input/200 output tokens for up to three movies. Input assumptions include instructions, schemas, and retrieved context. These are planning allowances, not measured usage.

| Item | Calculation | USD |
| --- | --- | ---: |
| Initial catalog embeddings | 300,000 / 1M × $0.02 | $0.0060 |
| Query embeddings | 200 × 50 / 1M × $0.02 | $0.0002 |
| Chat input, 400 calls total | 200 × 2,000 / 1M × $0.75 | $0.3000 |
| Chat output | 200 × 300 / 1M × $4.50 | $0.2700 |
| **Total** | **At the published rates above** | **$0.5762** |

This excludes retries, repeated evaluations/reindexing, longer prompts, taxes, currency conversion, hosting, and tracing charges. It assumes no caching or Batch discounts. A proposed $2 API allowance gives room for iteration within the provisional EUR 10 combined target, but is neither a billing cap nor spending authorization. Account eligibility, actual billing setup, and rate limits remain unverified; no EUR conversion is asserted.
