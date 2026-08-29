# HAKIM Ω — Enterprise Azure / Microsoft Foundry Provisioning Gate

Status: `BLOCKED-EXTERNAL`  
Owner: `Enterprise / Ministry of Education`  
Personal Azure trial: `PROHIBITED`  
Last assessed: 2026-08-29

## Purpose

Keep HAKIM development moving without binding production ownership, billing, or institutional data to a personal Azure account.

The gate is deliberately external: the application can be developed and tested before Azure Subscription provisioning, but production Foundry runtime and Microsoft 365 downstream access remain disabled until the institution provisions the required Azure resources and grants the minimum permissions.

## Current state

| Capability | State |
|---|---|
| Microsoft 365 identity | READY |
| Microsoft Entra tenant | READY |
| HAKIM login architecture | READY |
| Agent architecture | READY |
| GitHub CI/CD | READY |
| Enterprise Azure Subscription | `BLOCKED-EXTERNAL` |
| Microsoft Foundry project/runtime | `BLOCKED-EXTERNAL` |
| Foundry Agent Identity | `BLOCKED-EXTERNAL` |
| Microsoft Graph production access | `BLOCKED-EXTERNAL` |
| Teams / SharePoint / OneDrive production integration | `BLOCKED-EXTERNAL` |

## Non-negotiable ownership rule

Do **not** create an Azure Free Trial or personal subscription for the institutional HAKIM deployment.

The target ownership chain is:

`Ministry / Directorate tenant` → `Enterprise Azure Subscription` → `Resource Group` → `Microsoft Foundry` → `HAKIM Agent` → `Entra Agent Identity` → `Graph / Teams / SharePoint / OneDrive`

## Enterprise provisioning contract

The institution must provide the following identifiers after provisioning:

- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `FOUNDRY_RESOURCE_NAME`
- `FOUNDRY_PROJECT_NAME`
- `FOUNDRY_PROJECT_ENDPOINT`
- `HAKIM_AGENT_ID` (after agent creation/publishing)
- `HAKIM_AGENT_IDENTITY_ID` (after Foundry creates the agent identity)

No password, client secret, MFA code, or payment information belongs in this repository or in ChatGPT.

## Required enterprise controls

1. Azure Subscription is owned and billed by the institution.
2. Resource Group is institution-owned.
3. Microsoft Entra ID remains the workforce identity authority.
4. Foundry uses Entra/RBAC rather than API-key authentication for callers.
5. HAKIM uses least-privilege permissions for downstream resources.
6. Production agent identity is distinct from development identities when the agent is published.
7. Human-invoked Microsoft 365 actions use delegated/OBO authorization where appropriate.
8. Autonomous/background actions use the agent's own identity and explicit application permissions/RBAC.
9. Conditional Access, audit, ownership/sponsor and lifecycle controls are applied by the institution.
10. Secrets are never embedded in prompts, source code, workflow files, or repository data.

## Provisioning sequence

### Gate A — Azure ownership

Institution creates or assigns the enterprise Azure Subscription.

Acceptance evidence:

- Subscription ID exists.
- Subscription belongs to the institutional tenant/billing boundary.
- HAKIM deployment account has only the roles needed for provisioning.

### Gate B — Resource boundary

Create the dedicated HAKIM Resource Group.

Recommended logical naming:

`rg-hakim-<environment>`

Environments should be separated at least into `dev`, `test`, and `prod` when the institution is ready for them.

### Gate C — Microsoft Foundry

Create the institutional Microsoft Foundry resource/project inside the approved subscription and resource group.

Acceptance evidence:

- Foundry project opens successfully.
- Project endpoint is available.
- Entra authentication is enabled.
- Required Foundry RBAC assignments are present.

### Gate D — HAKIM agent identity

Create the first HAKIM agent in Foundry.

Foundry's current agent identity model provisions an Entra-based agent identity. Unpublished agents can share the project identity; published agents receive a dedicated identity. Production permission assignments must therefore be checked again after publishing.

Acceptance evidence:

- Agent ID is recorded.
- Agent identity ID is recorded.
- Owner/sponsor is recorded.
- The identity is visible to the institutional Entra administrators.

### Gate E — Microsoft Graph

Grant only the Graph permissions actually required by HAKIM's first production workflows.

Start with read-only access wherever possible. Add write permissions only for a demonstrated workflow that requires them.

Initial capability classes:

- User identity/profile resolution.
- SharePoint/OneDrive curriculum-file discovery and read.
- Teams context and approved interaction.
- Explicit document creation/update only when required.

Do not request tenant-wide write access as a shortcut.

### Gate F — Teams / SharePoint / OneDrive

Connect only institutional locations explicitly approved for HAKIM.

Acceptance evidence:

- A test teacher can authenticate with the institutional Microsoft 365 account.
- HAKIM resolves the user's identity and permitted scope.
- HAKIM can read an approved curriculum document.
- HAKIM cannot read an unapproved location.
- A write operation, if enabled, is auditable and limited to its approved destination.

### Gate G — Runtime assurance

Before production enablement, execute the HAKIM assurance suite:

1. Identity test.
2. Authorization boundary test.
3. Graph scope test.
4. Foundry invocation test.
5. Tool permission test.
6. Prompt/data isolation test.
7. Audit evidence test.
8. Failure/revocation test.
9. Published-agent identity regression test.
10. End-to-end teacher workflow test.

Production status is `GO` only when all required evidence exists.

## Development continues while the gate is blocked

The following work is explicitly independent of the Azure Subscription:

- HAKIM intent and planning contracts.
- Curriculum-source abstraction.
- Lesson/worksheet assessment schemas.
- Truth/evidence/completion gates.
- Permission policy model.
- Tool registry and capability contracts.
- Graph adapter interface and mock implementation.
- Foundry adapter interface and local/mock runtime.
- CI validation.
- End-to-end test fixtures.
- Audit/event schemas.
- Enterprise provisioning manifest.

The application must fail closed when a real enterprise capability is unavailable. A mock must never be presented as a production Microsoft connection.

## Evidence rule

`Configured` means configuration exists.  
`Reachable` means a real request succeeded.  
`Authorized` means the request succeeded under the intended least-privilege identity.  
`Proven` means the result is backed by retained test evidence.

These states must never be collapsed into one boolean such as `azure_ready=true`.

## External blocker definition

The gate is cleared only when the institution supplies a real Azure Subscription and the Foundry project is reachable under institutional identity.

Until then:

`Azure Subscription = NOT PROVISIONED`  
`Foundry Runtime = NOT PROVEN`  
`Graph/Teams = NOT PROVEN`

This is a controlled `BLOCKED-EXTERNAL`, not a development failure.
