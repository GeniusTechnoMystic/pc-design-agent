# Provenance and Compatibility Best Practices

## Provenance

- Every important fact should have a source URL.
- Keep raw captures when the source may change later.
- Use retrieval timestamps on all volatile data.
- Preserve conflicting facts if confidence is low.

## Compatibility

- Model protocols and connectors explicitly.
- Keep separate layers for physical, electrical, firmware, driver, and workload compatibility.
- Encode hard failures separately from advisory warnings.
- Add evidence links to every non-obvious compatibility rule.

## Pricing

- Store asking, shipping, and landed cost separately.
- Track condition and seller quality for used parts.
- Use medians and volatility, not only a single latest price.
