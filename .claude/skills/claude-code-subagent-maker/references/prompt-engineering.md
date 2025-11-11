# Prompt Engineering for Subagents

This guide covers how to write effective system prompts for Claude Code subagents.

## Core Principles

### 1. Be Specific and Directive

**Weak:**
> You help with code review.

**Strong:**
> You are a senior code reviewer. When invoked, immediately run `git diff` to identify changes, then review them focusing on security, maintainability, and performance. Provide specific, actionable feedback organized by priority.

### 2. Include Process Steps

Always include numbered "When invoked" steps that tell the subagent exactly what to do:

```markdown
## When Invoked

1. Run `git diff` to see recent changes
2. Identify files that need review
3. For each file, check against quality criteria
4. Provide organized feedback with examples
5. Suggest specific improvements with code samples
```

### 3. Provide Decision Frameworks

Give subagents frameworks for making decisions:

```markdown
## Severity Assessment

Classify issues by impact:
- **Critical**: Security vulnerabilities, data loss, crashes
- **High**: Performance issues, significant bugs, poor UX
- **Medium**: Code quality, minor bugs, missing tests
- **Low**: Style issues, documentation, minor optimizations
```

### 4. Use Concrete Examples

Show examples of good and bad patterns:

```markdown
## Code Quality Examples

**Good naming:**
```python
def calculate_user_total_price(items, tax_rate):
    return sum(item.price for item in items) * (1 + tax_rate)
```

**Poor naming:**
```python
def calc(x, y):
    return sum(a.b for a in x) * (1 + y)
```
```

### 5. Define Output Format

Specify exactly how output should be structured:

```markdown
## Output Format

For each issue found:

**[ISSUE TITLE]** [Location]
Severity: [Critical/High/Medium/Low]

Description: [What's wrong]
Impact: [Why it matters]
Fix: [Specific solution with code]
```

## Prompt Structure Template

```markdown
You are a [ROLE] specializing in [DOMAIN].

## When Invoked

1. [First action]
2. [Second action]
3. [Continue...]

## [Core Framework/Checklist]

[Structured guidance on what to check/do]

## [Process/Methodology]

[Step-by-step process to follow]

## Output Format

[Specific format for deliverables]

## Best Practices

✅ Do: [Positive examples]
❌ Don't: [Negative examples]
```

## Prompt Patterns

### Pattern 1: The Systematic Reviewer

Use for: Code review, security audits, quality checks

```markdown
You are a systematic code reviewer.

## When Invoked

1. Identify scope (what changed)
2. Apply checklist systematically
3. Document findings with evidence
4. Provide fix recommendations

## Review Checklist

Go through each category:
- [ ] Security: [specific checks]
- [ ] Quality: [specific checks]
- [ ] Performance: [specific checks]

For each issue:
1. Cite specific line numbers
2. Explain the problem
3. Show how to fix it
4. Explain why fix is better
```

### Pattern 2: The Problem Solver

Use for: Debugging, troubleshooting, optimization

```markdown
You are a systematic problem solver.

## When Invoked

1. Gather all relevant information
2. Form hypothesis about root cause
3. Test hypothesis with minimal changes
4. Verify solution works
5. Document reasoning

## Problem-Solving Process

Step 1: Information Gathering
- Run diagnostics
- Check recent changes
- Review error messages

Step 2: Hypothesis Formation
- Based on evidence, hypothesize cause
- Make hypothesis specific and testable

Step 3: Testing
- Make minimal change to test hypothesis
- Verify results confirm or refute hypothesis

Step 4: Solution
- Implement fix for root cause
- Verify fix resolves issue
- Check for regressions
```

### Pattern 3: The Builder

Use for: Creating new code, implementing features

```markdown
You are an expert builder of [SPECIFIC THING].

## When Invoked

1. Understand requirements clearly
2. Plan implementation approach
3. Build incrementally
4. Test as you go
5. Document important decisions

## Implementation Checklist

Before coding:
- [ ] Requirements are clear
- [ ] Approach is sound
- [ ] Edge cases identified

During coding:
- [ ] Follow project patterns
- [ ] Write tests
- [ ] Handle errors

After coding:
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No regressions
```

## Advanced Techniques

### Conditional Logic

```markdown
## Decision Tree

IF error is in test file:
  → Run just that test with verbose output
  → Analyze why test expectation isn't met
  
ELSE IF error is exception/crash:
  → Check stack trace for root cause
  → Add debug logging at failure point
  
ELSE IF error is logic bug:
  → Add assertions to narrow location
  → Use debugger to inspect state
```

### Self-Correction Prompts

```markdown
## Quality Check

Before providing output:
1. Review your own recommendations
2. Verify code examples are correct
3. Check that fixes actually solve the problem
4. Ensure you haven't missed edge cases
```

### Scope Management

```markdown
## What NOT to Do

Don't:
- Review unchanged files unless asked
- Suggest changes outside problem scope
- Fix unrelated issues
- Make large refactors during debugging
- Suggest changes contradicting project patterns

Stay focused on the specific task.
```

## Common Mistakes to Avoid

### ❌ Mistake: Vague Instructions

```markdown
You help with testing.
```

**Problem:** No guidance on what to do, when, or how.

### ✅ Solution: Specific Instructions

```markdown
You are a test automation expert who runs tests after code changes.

When invoked:
1. Identify which tests to run based on changed files
2. Run tests with appropriate flags
3. If failures occur, analyze and fix them
4. Verify fixes don't break other tests
```

### ❌ Mistake: Missing Process Steps

```markdown
You review code for quality.
```

**Problem:** Doesn't explain HOW to review.

### ✅ Solution: Clear Process

```markdown
You review code for quality.

Process:
1. Run `git diff` to see changes
2. Check each change against quality criteria:
   - Naming is clear
   - Logic is simple
   - Tests are present
   - No security issues
3. Provide feedback with examples
```

### ❌ Mistake: No Examples

```markdown
Check for security issues.
```

**Problem:** Unclear what constitutes a security issue.

### ✅ Solution: Provide Examples

```markdown
Check for security issues:

**SQL Injection:**
```python
# BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Exposed Secrets:**
```python
# BAD
API_KEY = "sk_live_abc123"

# GOOD
API_KEY = os.environ.get('API_KEY')
```
```

## Testing Your Prompts

### 1. Read Aloud Test

Read your prompt as if you're explaining to a colleague. Does it make sense? Is anything ambiguous?

### 2. Edge Case Test

Think of edge cases and check if your prompt addresses them:
- Empty inputs
- Very large inputs
- Error conditions
- Unusual but valid scenarios

### 3. Real Usage Test

Use the subagent on actual tasks. Does it do what you expected? Where does it struggle?

### 4. Iteration Test

After a few uses, what would you change? Add those improvements to the prompt.

## Examples of Great Prompts

### Example 1: Clear Role + Process + Output

```markdown
You are a Git workflow expert who creates well-formatted commit messages.

When invoked:
1. Run `git diff --staged` to see staged changes
2. Analyze the changes to understand what was done
3. Identify the type: feat, fix, docs, style, refactor, test, chore
4. Write a commit message following conventional commits

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(auth): add password reset functionality

- Implemented email-based password reset flow
- Added rate limiting to prevent abuse
- Created email templates for reset notifications

Closes #123
```
```

### Example 2: Checklist-Driven

```markdown
You are a deployment readiness checker.

When invoked:
1. Verify deployment checklist completion
2. Report any blockers
3. Provide go/no-go recommendation

Deployment Checklist:
- [ ] All tests passing (run `npm test`)
- [ ] No console.log statements (grep -r "console.log")
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

Output:
```
DEPLOYMENT READINESS: [GO / NO-GO]

Checklist Results:
✅ Tests: All 47 passing
✅ Code quality: No console.logs found
❌ Migrations: Not tested yet - BLOCKER

Recommendation: NO-GO
Reason: Database migrations must be tested before deployment
Next step: Run migration against staging database
```
```

## Key Takeaways

1. **Be specific** - Vague prompts lead to vague outputs
2. **Show the process** - Step-by-step instructions work best
3. **Provide examples** - Concrete examples clarify expectations
4. **Define success** - Make it clear what good output looks like
5. **Include guardrails** - Tell the subagent what NOT to do
6. **Test and iterate** - Refine based on real usage
