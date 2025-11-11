---
name: claude-code-subagent-maker
description: Expert guide for creating specialized Claude Code subagents. Use when users want to create, customize, or improve subagents for Claude Code - including generating initial subagent configurations, defining tool permissions, writing effective system prompts, organizing subagents across project/user scopes, and implementing best practices for focused, reusable AI assistants that handle specific development tasks.
---

# Claude Code Subagent Maker

This skill provides comprehensive guidance for creating effective subagents in Claude Code - specialized AI assistants that handle specific development tasks with their own context windows, tool permissions, and custom system prompts.

## What Are Subagents?

Subagents are pre-configured AI personalities that Claude Code can delegate tasks to. Each subagent:

- Has a specific purpose and expertise area
- Uses its own context window separate from the main conversation
- Can be configured with specific tools it's allowed to use
- Includes a custom system prompt that guides its behavior


## Subagent Configuration

### File Format

```markdown
---
name: your-subagent-name
description: When this subagent should be invoked
tools: tool1, tool2, tool3  # Optional - inherits all tools if omitted
model: sonnet  # Optional - specify model alias or 'inherit'
---

Your subagent's system prompt goes here.
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier using lowercase letters and hyphens |
| `description` | Yes | Natural language description triggering delegation |
| `tools` | No | Comma-separated tool list. Omit to inherit all tools |
| `model` | No | Model alias (`sonnet`, `opus`, `haiku`) or `inherit` |

### File Locations

| Type | Location | Scope | Priority |
|------|----------|-------|----------|
| Project | `.claude/agents/` | Current project only | Highest |
| User | `~/.claude/agents/` | All projects | Lower |
| CLI | `--agents` flag | Current session | Medium |

Project-level subagents override user-level ones when names conflict.

## Core Design Principles

### 1. Single Responsibility

Create focused subagents with clear, specific purposes rather than trying to make one subagent do everything.

**Good:** A `test-runner` that runs tests and fixes failures  
**Bad:** A `dev-helper` that does testing, code review, debugging, and deployment

### 2. Proactive Descriptions

Write descriptions that encourage automatic delegation by including action-oriented language and clear triggers.

**Effective phrases:**
- "Use PROACTIVELY when..."
- "MUST BE USED for..."
- "Automatically invoke when..."
- "Use immediately after..."

**Examples:**

```markdown
# Good Description
description: Code review specialist. Use PROACTIVELY immediately after any code changes to review quality, security, and maintainability.

# Weak Description
description: Reviews code when asked
```

### 3. Detailed System Prompts

Include specific instructions, examples, workflows, and constraints. The more guidance you provide, the better the subagent performs.

**Essential elements:**
- Role definition ("You are a senior...")
- When invoked instructions (numbered steps)
- Checklists or frameworks to follow
- Output format specifications
- Priority guidelines
- Examples of good outcomes

### 4. Strategic Tool Access

Only grant tools necessary for the subagent's purpose. This improves security and helps the subagent focus.

**Common tool combinations:**
- Code review: `Read, Grep, Glob, Bash`
- Debugging: `Read, Edit, Bash, Grep, Glob`
- Testing: `Bash, Read, Edit, Grep`
- Data analysis: `Bash, Read, Write`

**View all available tools:** Use `/agents` command and select a subagent to edit - it shows all available tools including MCP tools.

### 5. Model Selection Strategy

Choose the appropriate model for each subagent's needs:

- `sonnet`: Default, balanced performance (recommended for most subagents)
- `opus`: Complex reasoning tasks requiring highest capability
- `haiku`: Fast, simple tasks where speed matters
- `inherit`: Match main conversation's model for consistency

## Subagent Workflow Patterns

### Pattern 1: Autonomous Reviewer

Subagents that automatically check work after completion.

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY immediately after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

When invoked:
1. Run `git diff` to see recent changes
2. Focus on modified files only
3. Begin review immediately without asking

Review checklist:
[specific criteria]

Provide organized feedback:
- Critical issues (must fix)
- Warnings (should fix)  
- Suggestions (nice to have)
```

### Pattern 2: Specialist Troubleshooter

Subagents that handle specific types of problems.

```markdown
---
name: debugger
description: Debugging specialist. Use PROACTIVELY when encountering errors, test failures, or unexpected behavior.
tools: Read, Edit, Bash, Grep, Glob
---

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Form hypothesis about root cause
4. Test hypothesis with targeted changes
5. Implement minimal fix
6. Verify solution
```

### Pattern 3: Domain Expert

Subagents with specialized knowledge for specific domains.

```markdown
---
name: data-scientist
description: SQL and BigQuery expert. Use for data analysis tasks, queries, and insights.
tools: Bash, Read, Write
model: sonnet
---

You specialize in data analysis with SQL and BigQuery.

When invoked:
1. Understand the analysis requirement
2. Write efficient, optimized queries
3. Use BigQuery CLI tools (bq) appropriately
4. Analyze and summarize results
5. Present findings with visualizations when helpful
```

## Advanced Features

### Chaining Subagents

For complex workflows, chain multiple subagents:

```
> Use the code-analyzer subagent to find performance issues, 
  then use the optimizer subagent to fix them
```

### Dynamic Selection

Claude Code intelligently selects subagents based on:
- Task description in your request
- Subagent `description` fields
- Current context and available tools

Make your descriptions specific and action-oriented for best results.

### MCP Tool Access

Subagents can access MCP server tools:
- When `tools` field is omitted, subagents inherit all MCP tools
- When `tools` is specified, you can explicitly list MCP tools
- Use `/agents` interface to see all available MCP tools

## Best Practices

### Do's

✅ Start with Claude-generated subagents, then customize  
✅ Write detailed, specific system prompts with examples  
✅ Use action-oriented language in descriptions  
✅ Limit tool access to what's necessary  
✅ Version control project subagents for team sharing  
✅ Test subagents on real tasks and iterate  
✅ Create focused subagents with single responsibilities  

### Don'ts

❌ Make overly generic subagents that do everything  
❌ Write vague descriptions like "helps with coding"  
❌ Grant all tools when only a few are needed  
❌ Forget to include "when invoked" instructions  
❌ Skip testing subagents on actual use cases  
❌ Duplicate functionality across multiple subagents  

## Templates and Examples

See `assets/templates/` for ready-to-use subagent templates:

- `code-reviewer.md` - Code review specialist
- `debugger.md` - Debugging expert
- `test-runner.md` - Test automation specialist
- `data-scientist.md` - SQL/data analysis expert
- `security-auditor.md` - Security review specialist
- `performance-optimizer.md` - Performance analysis expert
- `custom-template.md` - Blank template with all fields

See `references/` for additional guidance:

- `prompt-engineering.md` - Writing effective system prompts
- `tool-reference.md` - Complete list of available tools
- `real-world-examples.md` - Community subagent examples

## Managing Subagents

### Using /agents Command

```bash
/agents
```

This provides an interactive menu to:
- View all available subagents
- Create new subagents
- Edit existing subagents
- Delete custom subagents
- Manage tool permissions
- See which subagents are active

### Direct File Management

```bash
# List project subagents
ls .claude/agents/

# List user subagents
ls ~/.claude/agents/

# Edit a subagent
$EDITOR .claude/agents/code-reviewer.md

# Delete a subagent
rm .claude/agents/old-subagent.md
```

### CLI-based Configuration

Define subagents dynamically for testing:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer. Use proactively after code changes.",
    "prompt": "You are a senior code reviewer...",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

## Troubleshooting

### Subagent Not Being Invoked

**Problem:** Subagent exists but Claude Code doesn't use it.

**Solutions:**
- Make description more specific and action-oriented
- Add phrases like "Use PROACTIVELY" or "MUST BE USED"
- Mention specific trigger scenarios
- Test by explicitly requesting the subagent

### Subagent Lacks Context

**Problem:** Subagent doesn't have necessary information.

**Solutions:**
- Grant additional tools (especially `Read`, `Grep`, `Glob`)
- Improve system prompt with specific instructions
- Add examples of how to gather context
- Consider using `inherit` model if main conversation has relevant context

### Multiple Subagents Conflict

**Problem:** Multiple subagents trigger for the same task.

**Solutions:**
- Make descriptions more distinct and specific
- Use project-level override for specific cases
- Consider consolidating similar subagents
- Delete or disable unused subagents

## Performance Considerations

**Context Efficiency:** Subagents help preserve main context, enabling longer sessions.

**Latency:** Subagents start with clean slate and may add latency as they gather necessary context.

**Trade-off:** Use subagents for:
- Tasks that benefit from focused context
- Repeated workflows with specific patterns
- Operations that need different tool permissions
- Specialized domains requiring expert knowledge

## Creating Subagents: Complete Workflow

1. **Understand the need:** What specific task needs automation?
2. **Design the subagent:** What tools, model, and scope?
3. **Generate with Claude:** Use `/agents` to create initial version
4. **Customize:** Refine description and system prompt
5. **Test:** Try on real tasks
6. **Iterate:** Improve based on performance
7. **Share:** Commit project subagents or document user subagents

## Related Documentation

For more information, see Claude Code documentation:
- `/agents` command for interactive management
- Tool configurations and permissions
- MCP integration for external tools
- Plugin system for distributing subagents
