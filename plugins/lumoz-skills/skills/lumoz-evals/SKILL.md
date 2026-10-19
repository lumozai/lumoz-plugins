---
name: lumoz-evals
description: Create repo-specific regression evals from Lumoz problem or business task eval suggestions fetched through the Lumoz MCP server. Use when asked to turn a Lumoz eval suggestion, RCA, problem, business task, or tool-correctness issue into a DeepEval/pytest/customer-repo eval framework.
metadata:
  short-description: Author evals from Lumoz eval suggestions
---

# Lumoz Evals From Problems

Use this skill when the task is to create an eval from a Lumoz problem/RCA/task eval suggestion. The goal is to convert Lumoz's observed telemetry and failure evidence into a repository-native regression eval that a customer can run and maintain.

## Required Lumoz Context

Fetch the eval suggestion through the Lumoz MCP tools before editing tests:

- If you only know the app: call `list_app_eval_suggestions(app_id, environment, ...)` and choose the relevant row.
- If you know the problem: call `list_problem_eval_suggestions(app_id, problem_id, environment)`.
- For implementation: call `get_problem_eval_suggestion(app_id, problem_id, eval_suggestion_id, environment)`.
- If you know the business task name but not its ID/version: call `list_business_tasks(app_id, environment)` and choose the relevant task row.
- If you know the Business Task: call `list_business_task_eval_suggestions(app_id, task_id, environment, task_version=...)`. This returns existing telemetry-based suggestions or generates them if none exist.
- If you know the eval suggestion ID: call `get_business_task_eval_suggestion(app_id, task_id, eval_suggestion_id, environment, task_version=...)`.

The detail payload is the source of truth. It may come from `get_problem_eval_suggestion`, `get_business_task_eval_suggestion`, or the detailed suggestions returned by `list_business_task_eval_suggestions`. Use:

- `eval_spec` for the intended assertions and failure mode.
- `trace_set.primary_failure` for the canonical failing example. For business task telemetry suggestions this field may contain seed/reference traces, not necessarily failures.
- `trace_set.similar_failures` for additional examples or variants.
- `trace_set.known_good_contrasts` for negative controls when available.
- `implementation_prompt` and `limitations` for guardrails.
- For problem suggestions: `source_classifier_key`, `source_subtype`, `representative_trace_id`, `problem_id`, and `eval_suggestion_id` for provenance.
- For Business Task suggestions: `task_id`, `task_version`, `source_pattern_key`, `source_pattern_type`, `representative_trace_id`, and `eval_suggestion_id` for provenance.

Do not invent missing evidence. If the payload lacks tool schemas, final response, known-good contrasts, or unredacted content, preserve that limitation in the eval or state that the eval can only cover the available evidence.

## Repository Discovery

Before writing an eval, inspect the target repo for existing conventions:

- Existing eval frameworks: DeepEval, pytest, unittest, vitest, custom harnesses.
- Existing test data fixture patterns.
- How the app invokes agents/tools and whether tool calls can be mocked.
- Existing CI commands or test scripts.

Prefer the repo's existing evaluation style. Use DeepEval when the repo already uses it or the user explicitly asks for it. If there is no eval framework, create the smallest maintainable pytest-compatible eval wrapper rather than introducing a large framework.

## Eval Construction

Build the eval around the behavior Lumoz observed, not around implementation details that may change.

- Use the primary failure as the minimum regression case.
- Add similar failures as parametrized cases when they differ meaningfully.
- Add known-good contrasts as negative controls when available.
- Mock external tools/services deterministically.
- Assert both the bad behavior and the desired behavior when the repo exposes both.
- Keep expected outputs specific enough to catch the regression, but not so brittle that harmless wording changes fail the eval.

For tool-correctness suggestions:

- `tool_hallucination`: verify the agent does not claim a tool was called, completed, or returned data unless an actual tool invocation/result exists.
- `tool_parameter_error`: verify the agent sends schema-valid, semantically correct arguments or handles parameter uncertainty instead of fabricating values.
- `wrong_tool_selected`: verify the agent selects the appropriate tool for the user's intent and available schemas.
- `tool_success_semantic_failure`: verify empty/null/error-like successful tool responses are not treated as successful evidence.

## Output Requirements

The final change should include:

- The eval/test file using the repo's conventions.
- Any minimal fixtures or mocks needed to make the eval runnable.
- Provenance in test metadata or comments: Lumoz  app id, environment, `eval_suggestion_id`, representative trace ID, and either `problem_id` or Business Task identity (`task_id`, `task_version`, and `source_pattern_key`).
- A short note on limitations if the Lumoz payload was partial or redacted.

Run the narrowest relevant test/eval command if dependencies are available. If you cannot run it, report the exact command that should be run and why it was not executed.


## Boundaries

- Do not call mutation tools or force-regenerate Lumoz eval suggestions unless the user explicitly asks. Calling `list_business_task_eval_suggestions` may generate missing business task suggestions; that is the expected read path.
- Do not change production application logic unless the user asks for a fix in addition to the eval.
- Do not tailor the eval to opaque text tokens from one trace when a structural assertion is possible.
- Do not assume DeepEval-specific structure from the Lumoz payload; adapt the generic spec to the repo's chosen framework.
