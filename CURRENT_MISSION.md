# HAKIM Ω — Current Mission

## Mission
Build HAKIM as a provider-independent educational agent that works without Azure, Foundry, Graph, Teams, approvals, or payment, while remaining ready for enterprise adapters when those capabilities become available.

## Current phase
CORE-INDEPENDENT-RUNTIME

## Completed
- Enterprise Azure / Foundry provisioning boundary defined.
- Personal Azure trial explicitly excluded from institutional architecture.
- Fail-closed enterprise gate implemented.
- Machine-readable enterprise provisioning manifest implemented.
- Enterprise gate tests implemented.
- CI workflow added.

## Active objective
Complete the provider-independent runtime and continuity layer.

## Non-blocking external capabilities
- Azure Subscription
- Microsoft Foundry
- Entra Agent Identity
- Microsoft Graph
- Teams
- SharePoint / OneDrive

## Rule
External capabilities are optional adapters. Their absence must not prevent core HAKIM from running.

## Resume protocol
On every new execution session:
1. Read this file.
2. Read PROJECT_STATE.md.
3. Read NEXT_ACTION.md.
4. Inspect the latest repository commits and CI evidence.
5. Continue from the first unproven NEXT_ACTION.
6. Never claim a capability is proven without execution evidence.
