# Coverage Analysis

**Purpose:** Gap analysis between API code and documentation, plus recommendations for wrapper priorities

---

## Summary

The Dataiku Python API is **comprehensive and well-structured** with strong coverage across all major areas. This analysis identifies what's documented, what gaps exist, and priorities for wrapper development.

---

## Coverage by Category

| Category | API Coverage | Doc Coverage | Notes |
|----------|-------------|--------------|-------|
| **Client & Auth** | ✓✓✓ Complete | ✓✓✓ Excellent | Well documented, multiple auth methods |
| **Projects** | ✓✓✓ Complete | ✓✓ Good | 150+ methods, most documented |
| **Datasets** | ✓✓✓ Complete | ✓✓ Good | All types covered, some advanced features light |
| **Recipes** | ✓✓✓ Complete | ✓✓ Good | Visual recipes well covered, code recipes adequate |
| **Scenarios** | ✓✓✓ Complete | ✓✓ Good | Core functionality documented |
| **Jobs & Futures** | ✓✓✓ Complete | ✓ Adequate | Async patterns could be clearer |
| **ML & Models** | ✓✓✓ Complete | ✓✓ Good | Training documented, evaluation stores less so |
| **Admin** | ✓✓✓ Complete | ✓ Adequate | Users/groups good, instance settings sparse |
| **API Node** | ✓✓ Good | ✓ Adequate | Deployment documented, advanced features light |
| **Govern** | ✓✓ Good | ✓ Light | Newer feature, documentation growing |
| **Fleet Mgmt** | ✓ Basic | ✓ Light | Cloud-specific, docs scattered |
| **Plugins** | ✓✓ Good | ✓✓ Good | Component classes well documented |

Legend: ✓✓✓ Complete | ✓✓ Good | ✓ Adequate | ⚠ Light

---

## What's in API but Lightly Documented

### 1. Advanced Dataset Features

**Exists in API:**
- Dataset metrics computation
- Custom partitioning schemes
- Advanced format parameters
- Dataset-level permissions
- Data quality rules
- Column-level metadata

**Documentation Status:** Sparse examples

**Recommendation:** High priority for wrapper - common use case

### 2. Flow Graph Operations

**Exists in API:**
- Flow zone manipulation
- Node dependency analysis
- Flow graph export/import
- Flow variable propagation
- Shared objects management

**Documentation Status:** Basic operations only

**Recommendation:** Medium priority - advanced users

### 3. ML Evaluation Stores

**Exists in API:**
- Model evaluation tracking
- Performance comparison
- Drift analysis
- Evaluation dataset management
- Custom metric tracking

**Documentation Status:** Light documentation

**Recommendation:** High priority - MLOps use case

### 4. Saved Model Advanced Features

**Exists in API:**
- Model versioning strategies
- A/B testing setup
- Champion/challenger patterns
- Model performance tracking
- Conditional deployment

**Documentation Status:** Basic deployment only

**Recommendation:** High priority - production ML

### 5. LangChain Integration

**Exists in API:**
- LLM Mesh integration
- Agent tracing
- Prompt management
- LLM conversation tracking

**Documentation Status:** New feature, docs minimal

**Recommendation:** Medium priority - emerging use case

### 6. Instance Administration

**Exists in API:**
- License management
- System diagnostics
- Resource monitoring
- Backup/restore operations
- Security auditing

**Documentation Status:** Admin docs scattered

**Recommendation:** Low priority - admin-specific

---

## Inconsistencies Found

### 1. Naming Conventions

**Issue:** Some inconsistency between:
- `list_*` vs `get_*` methods
- `get_settings()` vs `get_definition()`
- Recipe creators vs direct recipe creation

**Impact:** Medium - can confuse wrapper developers

**Recommendation:** Document patterns clearly in wrapper

### 2. Return Type Variations

**Issue:** Some methods return:
- Dicts (raw JSON)
- Objects (class instances)
- Lists of dicts vs lists of objects
- Sometimes inconsistent across similar operations

**Impact:** Medium - type hints needed in wrapper

**Recommendation:** Normalize return types in wrapper layer

### 3. Async Patterns

**Issue:** Multiple async patterns:
- `build(wait=True/False)`
- `run()` returns trigger fire, then get scenario run (two-step)
- `DSSFuture` for some operations
- Direct polling for others

**Impact:** High - easy to misuse

**Recommendation:** Standardize async interface in wrapper

### 4. Settings Objects

**Issue:** Settings pattern is consistent but:
- Must remember to call `.save()`
- No validation before save
- Errors only on save, not on modification

**Impact:** Medium - common mistake

**Recommendation:** Wrapper should auto-save or validate

---

## Gaps in Code Examples

### High Priority Gaps

1. **End-to-End Workflows**
   - Complete ETL pipeline example
   - Full ML workflow (train → evaluate → deploy → monitor)
   - Multi-project automation

2. **Error Recovery Patterns**
   - Handling failed builds
   - Retry logic for transient errors
   - Rollback on failure

3. **Performance Optimization**
   - Bulk operations
   - Parallel execution patterns
   - Memory-efficient data processing

4. **Testing Patterns**
   - How to test code that uses API
   - Mock/stub patterns
   - Integration test examples

### Medium Priority Gaps

5. **Advanced Recipe Patterns**
   - Dynamic recipe generation
   - Programmatic schema updates
   - Complex join configurations

6. **Security Patterns**
   - API key rotation
   - Permission checking before operations
   - Secure credential handling

7. **Monitoring & Alerting**
   - Job failure detection
   - Performance monitoring
   - Resource usage tracking

---

## Recommendations for Wrapper Framework

### Tier 1: Must Have (Core Framework)

**Priority:** Implement immediately

1. **Unified Client**
   - Single entry point
   - Connection pooling
   - Automatic retry logic
   - Better error messages

2. **Dataset Operations**
   - Simplified CRUD
   - Type-safe schema management
   - Efficient data access
   - Auto-schema updates

3. **Recipe Builder**
   - Fluent API for recipe creation
   - Type-safe configuration
   - Automatic schema propagation
   - Validation before save

4. **Job Management**
   - Unified async interface
   - Progress tracking
   - Auto-polling with callbacks
   - Error handling

5. **Settings Management**
   - Auto-save on modification
   - Validation before save
   - Diff/rollback support
   - Type safety

### Tier 2: Should Have (Enhanced Features)

**Priority:** Implement soon

6. **Scenario Builder**
   - Fluent API for steps
   - Type-safe trigger configuration
   - Testing utilities
   - Run history analysis

7. **Project Templates**
   - Quick project creation from templates
   - Standard patterns (ETL, ML, reporting)
   - Best practice defaults

8. **ML Workflow**
   - Train → evaluate → deploy pipeline
   - Model versioning helpers
   - Drift detection
   - A/B testing setup

9. **Batch Operations**
   - Bulk dataset creation
   - Parallel job execution
   - Multi-project operations

10. **Testing Utilities**
    - Mock DSS client
    - Test data generators
    - Validation helpers

### Tier 3: Nice to Have (Advanced)

**Priority:** Implement later

11. **Flow Analysis**
    - Dependency visualization
    - Impact analysis
    - Optimization suggestions

12. **Admin Tools**
    - User/group management
    - Resource monitoring
    - Audit logging

13. **Plugin Development**
    - Plugin templates
    - Component builders
    - Testing frameworks

---

## API Maturity Assessment

### Strengths

✓ **Comprehensive Coverage** - API covers almost everything DSS can do
✓ **Consistent Patterns** - List/Get, Settings, Futures are standardized
✓ **Well Typed** - Method signatures are clear
✓ **Stable** - API is mature and stable across versions
✓ **Documented** - Core functionality has good documentation

### Weaknesses

⚠ **Async Complexity** - Multiple async patterns can be confusing
⚠ **Type Hints** - Limited type annotations in some areas
⚠ **Settings Mutability** - Easy to forget `.save()` calls
⚠ **Error Messages** - Some errors could be more helpful
⚠ **Advanced Features** - Less documentation for advanced use cases

### Opportunities for Wrapper

🎯 **Simplify Async** - Uniform interface for all async operations
🎯 **Add Validation** - Catch errors before API calls
🎯 **Better Types** - Full type hints throughout
🎯 **Smart Defaults** - Reduce boilerplate
🎯 **Helper Methods** - Common patterns as single method calls
🎯 **Testing Support** - Make API code testable

---

## Wrapper Development Roadmap

### Phase 1: Core (Weeks 1-4)

- [ ] Unified client with connection management
- [ ] Dataset operations (CRUD, schema, build)
- [ ] Recipe execution and monitoring
- [ ] Basic job management
- [ ] Settings auto-save

**Deliverable:** Can build simple ETL pipelines

### Phase 2: Enhanced (Weeks 5-8)

- [ ] Recipe builders (Join, Group, etc.)
- [ ] Scenario creation and execution
- [ ] Advanced job monitoring
- [ ] Batch operations
- [ ] Error recovery patterns

**Deliverable:** Can build complex automated pipelines

### Phase 3: Advanced (Weeks 9-12)

- [ ] ML workflow helpers
- [ ] Project templates
- [ ] Flow analysis
- [ ] Testing utilities
- [ ] Performance optimization

**Deliverable:** Production-ready framework

---

## Conclusion

The Dataiku Python API is **well-designed and comprehensive**. A wrapper framework should focus on:

1. **Simplifying common patterns** (80% of use cases)
2. **Standardizing async operations** (biggest pain point)
3. **Adding validation and type safety** (prevent errors)
4. **Providing templates and helpers** (accelerate development)

The API provides everything needed - a wrapper just needs to make it more ergonomic and less error-prone.

---

**Last Updated:** 2025-11-21
**Based on API Version:** 14.1.3+
