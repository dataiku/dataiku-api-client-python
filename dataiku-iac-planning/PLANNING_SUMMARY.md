# Dataiku IaC - Planning Summary

**Document Date:** 2025-11-23
**Status:** Planning Complete, Ready for POC
**Next Step:** Review and approve for POC development

---

## Executive Summary

This planning package contains comprehensive documentation for **Dataiku IaC** - a declarative, Git-native infrastructure-as-code solution for Dataiku that addresses enterprise DevOps team requirements.

### The Problem

Enterprise DevOps teams are currently blocked from adopting Dataiku due to:
1. **No infrastructure-as-code support** - All configuration is imperative and UI-based
2. **Poor CI/CD integration** - Manual processes prevent GitOps workflows
3. **State management issues** - No HA on Automation/Design nodes, no recovery from failures
4. **Lack of testing framework** - Cannot validate pipelines before deployment
5. **Manual environment promotion** - Connection remapping requires manual clicks

### The Solution

Build an **external orchestration layer** that provides:
- ✅ **Declarative YAML/Python configs** - Describe desired state, not steps
- ✅ **Git-based workflows** - Version control, rollback, collaboration
- ✅ **Plan/Apply workflow** - Preview changes before execution (Terraform-style)
- ✅ **External state management** - Track deployments, detect drift, enable recovery
- ✅ **Testing framework** - Validate pipelines without deploying to production
- ✅ **Automatic remapping** - Handle environment differences programmatically
- ✅ **CI/CD native** - GitHub Actions, GitLab CI, Jenkins templates
- ✅ **Govern integration** - Approval workflows for technical and business stakeholders

### Business Impact

**Target Outcomes:**
- Transform Dataiku from "nice-to-have" to "running analytics environments"
- Enable enterprise adoption by DevOps-focused organizations
- Compete effectively with dbt for developer mindshare
- Reduce deployment errors by 70% and deployment time by 80%

**Success Metrics:**
- 10+ enterprise customers adopted within 6 months of production release
- Developer NPS > 50
- Competitive win rate +20% vs Terraform/dbt shops

---

## Key Design Decisions

### 1. External State Management (Not Internal)

**Decision:** State stored externally in Git + S3, not in Dataiku's internal database

**Rationale:**
- Dataiku's tri-state architecture (filesystem + DB + Git) prevents proper HA
- External state enables recovery even when nodes fail
- Git provides version control and rollback
- S3 provides team collaboration and durability

**Impact:** Can't fix Dataiku's HA issues, but can work around them

### 2. Hybrid Configuration Format (YAML + Python)

**Decision:** Support both YAML for simplicity and Python DSL for complex logic

**Rationale:**
- YAML is accessible to all skill levels, great for version control
- Python DSL provides type safety, reusability, and expressiveness
- Teams can choose based on their needs

**Impact:** Slightly more implementation work, but much better UX

### 3. Pragmatic Evolution (Not Breaking Changes)

**Decision:** Build on top of existing Dataiku API without breaking it

**Rationale:**
- Backward compatibility ensures existing code keeps working
- Enables gradual adoption
- Lower risk than rewrite

**Impact:** Longer timeline, but safer path

### 4. DevOps-First Design

**Decision:** Target DevOps engineers as primary users, then data scientists, then data engineers

**Rationale:**
- DevOps teams are the current blockers to enterprise adoption
- Solving their problems unlocks broader adoption
- Features that help DevOps teams also help others

**Impact:** Focus on CI/CD, GitOps, state management, testing

### 5. Govern Integration is Core (Not Optional)

**Decision:** Deep integration with Govern for approval workflows

**Rationale:**
- Unique differentiator vs Terraform/dbt
- Enables both technical and business approvals
- Critical for enterprise compliance

**Impact:** Requires Govern API integration from Phase 3

---

## Documentation Index

### 📐 Architecture

| Document | Purpose | Status |
|----------|---------|--------|
| [01-overview.md](architecture/01-overview.md) | System architecture, components, data flow | ✅ Complete |
| [02-state-management.md](architecture/02-state-management.md) | State file format, storage, sync, locking | ✅ Complete |
| 03-execution-engine.md | Plan/apply engine, checkpointing, recovery | ⏳ TODO |
| 04-recovery-strategy.md | Failure recovery, rollback, disaster recovery | ⏳ TODO |
| 05-integration-points.md | Dataiku, Govern, CI/CD integration details | ⏳ TODO |

### 🎨 Design

| Document | Purpose | Status |
|----------|---------|--------|
| [01-config-format.md](design/01-config-format.md) | YAML/Python DSL format, validation, best practices | ✅ Complete |
| 02-state-file-format.md | State file schema, versioning, migration | ⏳ TODO |
| 03-validation-rules.md | Validation logic, error messages | ⏳ TODO |
| 04-error-handling.md | Error handling, recovery suggestions | ⏳ TODO |
| 05-testing-framework.md | Testing DSL, test execution, fixtures | ⏳ TODO |

### 🔌 API Specifications

| Document | Purpose | Status |
|----------|---------|--------|
| [01-cli-interface.md](api-specs/01-cli-interface.md) | Complete CLI specification with examples | ✅ Complete |
| 02-python-api.md | Programmatic Python API | ⏳ TODO |
| 03-config-schema.md | YAML schema definitions (JSON Schema) | ⏳ TODO |
| 04-state-api.md | State management API | ⏳ TODO |

### 🗺️ Roadmap

| Document | Purpose | Status |
|----------|---------|--------|
| [01-implementation-phases.md](roadmap/01-implementation-phases.md) | Detailed phased rollout plan with timelines | ✅ Complete |
| 02-poc-plan.md | 4-week POC detailed plan | ⏳ TODO |
| 03-dependencies.md | Technical and organizational dependencies | ⏳ TODO |
| 04-milestones.md | Key milestones, success criteria | ⏳ TODO |

### 🧪 Testing

| Document | Purpose | Status |
|----------|---------|--------|
| 01-unit-tests.md | Unit testing strategy | ⏳ TODO |
| 02-integration-tests.md | Integration testing approach | ⏳ TODO |
| 03-e2e-tests.md | End-to-end testing scenarios | ⏳ TODO |
| 04-user-acceptance.md | UAT criteria and process | ⏳ TODO |

### 💡 Examples

| Example | Purpose | Status |
|---------|---------|--------|
| [simple-project/](examples/simple-project/) | Minimal project showing basic concepts | ✅ Complete |
| ml-pipeline/ | ML workflow example | ⏳ TODO |
| multi-env/ | Complex multi-environment setup | ⏳ TODO |
| ci-cd-templates/ | GitHub Actions, GitLab CI examples | ⏳ TODO |

### 📝 Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| 001-state-storage.md | Where to store state (hybrid approach) | ⏳ TODO |
| 002-config-format.md | YAML + Python DSL | ⏳ TODO |
| 003-backward-compat.md | Pragmatic evolution strategy | ⏳ TODO |

### 🔬 Research

| Document | Purpose | Status |
|----------|---------|--------|
| api-coverage-analysis.md | Current API gaps and recommendations | ⏳ TODO |
| competitor-analysis.md | Terraform, dbt, Airflow comparison | ⏳ TODO |
| user-interviews.md | DevOps team feedback and requirements | ⏳ TODO |
| dataiku-internals.md | Dataiku architecture notes | ⏳ TODO |

---

## Implementation Timeline

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 0: POC                                    4 weeks     │
│ ████                                                        │
│                                                             │
│ Phase 1: Core IaC                               3-4 months │
│ ████████████                                                │
│                                                             │
│ Phase 2: Testing & Recovery                    2-3 months │
│ ████████                                                    │
│                                                             │
│ Phase 3: CI/CD & Govern                        2-3 months │
│ ████████                                                    │
│                                                             │
│ Phase 4: Advanced Features                     3-4 months │
│ ████████████                                                │
│                                                             │
│ TOTAL                                          12-18 months│
└─────────────────────────────────────────────────────────────┘

Milestones:
  • POC Complete:         Week 4
  • MVP (Alpha):          Month 4
  • Beta Release:         Month 7
  • Production Release:   Month 10
  • Full Feature Set:     Month 14
```

---

## Core Features by Phase

### Phase 0: POC (4 weeks)
- ✅ Basic state management
- ✅ Simple YAML configs
- ✅ Plan workflow
- ✅ Apply with checkpointing
- ✅ Demo scenario

### Phase 1: Core IaC (3-4 months)
- ✅ Full CLI (init, plan, apply, destroy)
- ✅ Projects, datasets, recipes, scenarios
- ✅ Environment management
- ✅ Variable substitution
- ✅ S3 state backend
- ✅ State locking
- ✅ Connection/code env remapping

### Phase 2: Testing & Recovery (2-3 months)
- ✅ Testing framework (schema, pipeline tests)
- ✅ Rollback capability
- ✅ Improved recovery
- ✅ Visual recipes support
- ✅ State backup/restore

### Phase 3: CI/CD & Govern (2-3 months)
- ✅ CI/CD templates (GitHub, GitLab, etc.)
- ✅ Govern approval integration
- ✅ ML models support
- ✅ Dashboards support
- ✅ Audit logging

### Phase 4: Advanced (3-4 months)
- ✅ Module system
- ✅ Performance optimization
- ✅ Python DSL
- ✅ Cost tracking
- ✅ Impact analysis

---

## Technology Stack

### Core Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **CLI Framework** | Click or Typer | Industry standard, excellent UX |
| **Config Format** | YAML + Python | Accessible + powerful |
| **State Storage** | JSON files | Human-readable, version-controllable |
| **Remote Backend** | S3 + DynamoDB | Durable, scalable, locking support |
| **Validation** | JSON Schema | Standard, well-supported |
| **Testing** | pytest | Standard Python testing framework |
| **CI/CD** | GitHub Actions | Most common platform |

### Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Core language |
| dataikuapi | 14.1.3+ | Dataiku Python API |
| pyyaml | 6.0+ | YAML parsing |
| jsonschema | 4.0+ | Config validation |
| click/typer | 8.0+ | CLI framework |
| boto3 | 1.26+ | S3/DynamoDB for state |
| pytest | 7.0+ | Testing |

---

## Target Users & Use Cases

### Primary: DevOps/Platform Engineers

**Pain Points:**
- Can't use standard GitOps workflows
- Manual environment promotion
- No preview of changes
- No recovery from failures

**Use Cases:**
1. Manage Dataiku projects via Git
2. Automate deployments in CI/CD
3. Preview changes before applying
4. Recover from failed deployments
5. Track and audit changes

### Secondary: Data Scientists

**Pain Points:**
- Too much clicking in UI
- Hard to replicate environments
- No version control for pipelines
- Testing requires production deployment

**Use Cases:**
1. Define pipelines in code
2. Version control ML workflows
3. Test locally before deploying
4. Collaborate via Git

### Tertiary: Data Engineers

**Pain Points:**
- Complex recipe configurations
- Manual schema management
- No automated testing
- Difficult to optimize pipelines

**Use Cases:**
1. Programmatically create complex recipes
2. Automated schema validation
3. Pipeline testing framework
4. Performance optimization

---

## Competitive Positioning

### vs Terraform

| Feature | Terraform | Dataiku IaC |
|---------|-----------|-------------|
| Declarative config | ✅ | ✅ |
| Plan/Apply workflow | ✅ | ✅ |
| State management | ✅ | ✅ |
| Module system | ✅ | ✅ (Phase 4) |
| Dataiku-specific | ❌ | ✅ |
| Testing framework | ⚠️ | ✅ |
| Govern integration | ❌ | ✅ |

**Positioning:** Terraform for Dataiku, but better integrated

### vs dbt

| Feature | dbt | Dataiku IaC |
|---------|-----|-------------|
| YAML configs | ✅ | ✅ |
| Git-native | ✅ | ✅ |
| Testing framework | ✅ | ✅ |
| Incremental builds | ✅ | ⚠️ (Phase 4) |
| Full ML lifecycle | ❌ | ✅ |
| Visual workflows | ❌ | ✅ |
| End-to-end platform | ❌ | ✅ |

**Positioning:** dbt for full ML/analytics platform, not just SQL transformations

### vs Manual Dataiku

| Feature | Manual | Dataiku IaC |
|---------|--------|-------------|
| Version control | ❌ | ✅ |
| Preview changes | ❌ | ✅ |
| Automated deployment | ❌ | ✅ |
| Testing before deploy | ❌ | ✅ |
| Environment consistency | ⚠️ | ✅ |
| Recovery from failures | ❌ | ✅ |
| Audit trail | ⚠️ | ✅ |

**Positioning:** Professional, production-ready way to use Dataiku

---

## Next Steps

### Immediate Actions (This Week)

1. **Review** this planning package with stakeholders
2. **Approve** (or provide feedback on) approach
3. **Allocate** engineer for POC (4 weeks full-time)
4. **Provision** test Dataiku instance
5. **Identify** 1-2 alpha customers

### Near-term (Next 4 Weeks)

1. **Execute** POC (see [roadmap/01-implementation-phases.md](roadmap/01-implementation-phases.md))
2. **Demo** POC to stakeholders
3. **Make go/no-go decision** on Phase 1
4. **Refine** Phase 1 requirements based on POC learnings
5. **Plan** resource allocation for Phase 1

### Medium-term (Months 2-4)

1. **Execute** Phase 1 (Core IaC)
2. **Alpha testing** with early customers
3. **Iterate** based on feedback
4. **Release** MVP/Alpha version

---

## Open Questions

### Technical

1. **State storage location:** S3 bucket organization? Per-org? Per-project?
2. **Lock timeout:** Default timeout value? Max timeout?
3. **Checkpoint granularity:** How often to checkpoint? Per-resource? Per-action?
4. **Test environment strategy:** Dedicated instance? Project cloning? Both?

### Product

5. **Pricing model:** Free? Paid tier? Enterprise-only?
6. **Support model:** Community support? Professional support?
7. **Update cadence:** Release schedule? LTS versions?
8. **Backward compatibility:** How long to support old versions?

### Business

9. **GTM strategy:** How to market to DevOps teams?
10. **Partner strategy:** Integrate with consulting partners?
11. **Training/certification:** Offer training programs?
12. **Success measurement:** How to track adoption and impact?

**These should be answered during POC and Phase 1.**

---

## Risk Assessment

### High Risk

- **Dataiku API limitations:** May discover needed APIs don't exist
  - **Mitigation:** Identify in POC, work with Dataiku team
- **DevOps adoption:** May not resonate with target users
  - **Mitigation:** Alpha program with real DevOps teams
- **State management complexity:** Could be more complex than anticipated
  - **Mitigation:** Start simple, iterate based on real-world use

### Medium Risk

- **Performance at scale:** May not scale to large projects
  - **Mitigation:** Benchmark early, optimize continuously
- **Migration challenges:** Existing Dataiku users may struggle
  - **Mitigation:** Excellent import/export, hybrid mode
- **Resource constraints:** May not have enough engineering capacity
  - **Mitigation:** Phased approach, clear priorities

### Low Risk

- **Competitive response:** Others may build similar tools
  - **Mitigation:** Fast iteration, Govern differentiation
- **Technology changes:** Core dependencies may change
  - **Mitigation:** Standard, stable technologies chosen

---

## Success Criteria

### POC Success (Week 4)

- [ ] Can manage 1 project, 2 datasets, 1 recipe via IaC
- [ ] Plan accurately shows what will change
- [ ] Apply creates resources correctly
- [ ] State file updates properly
- [ ] Can resume interrupted apply
- [ ] Stakeholders approve to proceed

### MVP Success (Month 4)

- [ ] 2+ alpha customers using successfully
- [ ] Can manage complete project via IaC
- [ ] Documentation is comprehensive
- [ ] DevOps teams provide positive feedback
- [ ] Ready for broader beta testing

### Production Success (Month 10)

- [ ] 10+ enterprise customers adopted
- [ ] Developer NPS > 50
- [ ] Deployment time reduced 80%
- [ ] Deployment errors reduced 70%
- [ ] Clear differentiation vs competitors

---

## Appendix: Command Examples

### Quick Start

```bash
# Install
pip install dataikuapi[iac]

# Initialize project
dataiku-iac init --from-existing MY_PROJECT

# Configure environments
# Edit environments/dev.yml and environments/prod.yml

# Plan deployment to dev
dataiku-iac plan -e dev

# Apply to dev
dataiku-iac apply -e dev

# Run tests
dataiku-iac test -e dev

# Deploy to prod (with approval)
dataiku-iac plan -e prod
# Submit to Govern for approval
dataiku-iac apply -e prod  # Blocked until approved
```

### Typical CI/CD Workflow

```yaml
# .github/workflows/dataiku.yml
name: Dataiku Deploy

on:
  pull_request:
  push:
    branches: [main]

jobs:
  plan:
    if: github.event_name == 'pull_request'
    steps:
      - run: dataiku-iac plan -e prod

  test:
    steps:
      - run: dataiku-iac test -e test

  deploy:
    if: github.event_name == 'push'
    needs: test
    steps:
      - run: dataiku-iac apply -e prod --auto-approve
```

---

**Planning Complete:** 2025-11-23
**Next Milestone:** POC Week 1 Kickoff
**Document Owner:** Development Team
**Review Cycle:** Weekly during POC, monthly during development
