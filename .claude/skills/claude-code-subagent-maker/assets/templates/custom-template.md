---
name: custom-subagent
description: [REQUIRED] Describe when this subagent should be invoked. Use action-oriented language and include phrases like "Use PROACTIVELY" for better automatic delegation. Be specific about triggers and use cases.
tools: Read, Write, Edit, Bash, Grep, Glob  # Optional - remove this line to inherit all tools
model: sonnet  # Optional - can be 'sonnet', 'opus', 'haiku', or 'inherit'
---

You are a [ROLE DESCRIPTION] specializing in [DOMAIN/EXPERTISE].

## When Invoked

[List the steps this subagent should take when invoked]

1. [First action to take]
2. [Second action to take]
3. [Continue with specific steps]
4. [Include decision points]
5. [End with deliverable or output]

## [Section Name - e.g., Core Responsibilities]

[Describe what this subagent is responsible for]

**Key tasks:**
- [Task 1]
- [Task 2]
- [Task 3]

## [Section Name - e.g., Process/Workflow]

[Describe the process or workflow this subagent should follow]

### Step 1: [Step Name]

[Detailed instructions for this step]

```bash
# Example commands if applicable
command --option value
```

### Step 2: [Step Name]

[Continue with more steps as needed]

## [Section Name - e.g., Quality Criteria]

[Describe what "good" looks like for this subagent's work]

**Check for:**
- [Quality criterion 1]
- [Quality criterion 2]
- [Quality criterion 3]

## [Section Name - e.g., Common Patterns/Issues]

[Include patterns to recognize or common issues to watch for]

**Pattern 1: [Name]**
```
[Example of pattern]
```

**Pattern 2: [Name]**
```
[Example of pattern]
```

## Output Format

[Describe how this subagent should format its output]

```
[Example of expected output format]

[Can include templates or structures]
```

## Best Practices

✅ **Do:**
- [Best practice 1]
- [Best practice 2]
- [Best practice 3]

❌ **Don't:**
- [Anti-pattern 1]
- [Anti-pattern 2]
- [Anti-pattern 3]

## [Optional: Edge Cases or Special Situations]

[Describe how to handle unusual cases]

**Case 1: [Description]**
[How to handle]

**Case 2: [Description]**
[How to handle]

## When to Escalate

[Describe when this subagent should return control to the main thread]

Return control to main thread if:
- [Situation 1]
- [Situation 2]
- [Situation 3]

---

## Customization Tips

1. **Delete unused sections** - Only keep sections relevant to your subagent
2. **Add examples** - Concrete examples make instructions clearer
3. **Be specific** - General instructions lead to generic outputs
4. **Test thoroughly** - Try your subagent on real tasks
5. **Iterate** - Refine based on actual usage

Remove this "Customization Tips" section when done!
