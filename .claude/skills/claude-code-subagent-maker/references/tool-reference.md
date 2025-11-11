# Tool Reference for Subagents

This guide covers available tools for Claude Code subagents and when to use them.

## How Tools Work

### Tool Inheritance

**Option 1: Inherit all tools (recommended for most subagents)**
```markdown
---
name: my-subagent
description: ...
# No 'tools' field - inherits all tools including MCP tools
---
```

**Option 2: Specific tools only**
```markdown
---
name: my-subagent
description: ...
tools: Read, Write, Edit, Bash, Grep, Glob
---
```

### Viewing Available Tools

Use the `/agents` command to see all available tools including MCP tools:
```
/agents
```

Select a subagent to edit and you'll see the complete list of available tools.

## Core Claude Code Tools

### Read
**Purpose:** Read file contents

**When to grant:**
- Subagents that need to examine code
- Review and analysis tasks
- Debugging and troubleshooting
- Any task requiring file inspection

**Typical use cases:**
- Code reviewers reading changed files
- Debuggers inspecting source code
- Analyzers examining configuration files

```python
# Typical usage
content = read_file("src/app.py")
```

### Write
**Purpose:** Create new files

**When to grant:**
- Subagents that generate code or documentation
- Creating test files
- Generating configuration files
- Producing reports or outputs

**Typical use cases:**
- Test generators creating new test files
- Documentation writers creating .md files
- Build scripts creating configuration

**⚠️ Security consideration:** Can create files anywhere, so grant carefully.

### Edit
**Purpose:** Modify existing files

**When to grant:**
- Subagents that fix bugs
- Code formatters and refactorers
- Test fixers
- Configuration updaters

**Typical use cases:**
- Debuggers fixing code issues
- Formatters applying style changes
- Migration tools updating syntax

**⚠️ Security consideration:** Can modify any file, so grant carefully.

### Bash
**Purpose:** Execute shell commands

**When to grant:**
- Subagents that run tests
- Build and deployment tasks
- System diagnostics
- File operations beyond basic read/write

**Typical use cases:**
- Test runners executing `pytest` or `npm test`
- Analyzers running linters
- Debuggers checking git history

**Commands commonly used:**
```bash
# Running tests
pytest tests/
npm test
go test ./...

# Git operations
git diff
git log
git status

# File operations
find . -name "*.py"
grep -r "pattern" src/

# System info
which python
npm list --depth=0
```

**⚠️ Security consideration:** Can execute arbitrary commands. Most powerful and potentially dangerous tool.

### Grep
**Purpose:** Search file contents for patterns

**When to grant:**
- Subagents searching codebase
- Finding usages or references
- Security audits
- Code analysis

**Typical use cases:**
- Security auditors finding exposed secrets
- Refactorers finding all usages of a function
- Analyzers identifying patterns

```bash
# Common patterns
grep -r "TODO" src/
grep -r "password" --include="*.py" .
grep -n "class.*User" src/**/*.py
```

### Glob
**Purpose:** Find files matching patterns

**When to grant:**
- Subagents that work with multiple files
- File organization tasks
- Batch operations
- Codebase analysis

**Typical use cases:**
- Test runners finding all test files
- Linters checking all source files
- Documentation generators finding .md files

```bash
# Common patterns
**/*.py          # All Python files
src/**/test_*.py # All test files in src/
*.{js,ts}        # All JS and TS files
```

## Tool Combinations for Common Subagent Types

### Code Reviewer
```markdown
tools: Read, Grep, Glob, Bash
```

**Rationale:**
- `Read`: Examine file contents
- `Grep`: Search for patterns
- `Glob`: Find relevant files
- `Bash`: Run git diff, linters

**Doesn't need Write/Edit:** Reviews only, doesn't modify.

### Debugger
```markdown
tools: Read, Edit, Bash, Grep, Glob
```

**Rationale:**
- `Read`: Inspect code
- `Edit`: Fix bugs
- `Bash`: Run tests, check git history
- `Grep`: Find related code
- `Glob`: Find test files

**Needs Edit:** Must fix the bugs found.

### Test Runner
```markdown
tools: Bash, Read, Edit, Grep, Glob
```

**Rationale:**
- `Bash`: Run test commands
- `Read`: Examine test files and code
- `Edit`: Fix failing tests
- `Grep`: Search for test patterns
- `Glob`: Find test files

**Needs all tools:** Runs tests AND fixes failures.

### Security Auditor
```markdown
tools: Read, Grep, Glob, Bash
```

**Rationale:**
- `Read`: Examine code for vulnerabilities
- `Grep`: Search for exposed secrets, SQL injection patterns
- `Glob`: Find all relevant files
- `Bash`: Run security tools, check git history

**Doesn't need Write/Edit:** Identifies issues, doesn't fix them.

### Documentation Writer
```markdown
tools: Read, Write, Bash, Grep, Glob
```

**Rationale:**
- `Read`: Examine existing code and docs
- `Write`: Create new documentation files
- `Bash`: Run doc generation tools
- `Grep`: Find relevant code sections
- `Glob`: Find files to document

**Needs Write:** Creates new doc files.

### Code Formatter
```markdown
tools: Read, Edit, Bash, Glob
```

**Rationale:**
- `Read`: Check current formatting
- `Edit`: Apply format changes
- `Bash`: Run formatters like black, prettier
- `Glob`: Find files to format

**Needs Edit:** Modifies files.

### Data Analyst
```markdown
tools: Bash, Read, Write
```

**Rationale:**
- `Bash`: Run SQL queries, BigQuery CLI, data processing
- `Read`: Examine data files and schemas
- `Write`: Create analysis reports

**Minimal tools:** Focused on data operations.

## MCP Tools

MCP (Model Context Protocol) tools come from connected MCP servers. These can include:

- Database query tools
- API integration tools
- Custom business logic tools
- External service connectors

### Accessing MCP Tools

Subagents automatically inherit MCP tools when `tools` field is omitted. To grant specific MCP tools:

```markdown
---
name: my-subagent
description: ...
tools: Read, Write, mcp_database_query, mcp_api_call
---
```

Use `/agents` to see what MCP tools are available and their names.

## Security Considerations

### Risk Levels

**Low Risk:**
- `Read`: Can only read files
- `Grep`: Can only search
- `Glob`: Can only list files

**Medium Risk:**
- `Write`: Can create new files
- MCP tools: Varies by tool

**High Risk:**
- `Edit`: Can modify any file
- `Bash`: Can execute arbitrary commands

### Principle of Least Privilege

Grant only the tools needed for the subagent's specific purpose:

✅ **Good:**
```markdown
# Code reviewer - reads but doesn't modify
tools: Read, Grep, Glob, Bash
```

❌ **Bad:**
```markdown
# Code reviewer with unnecessary permissions
tools: Read, Write, Edit, Bash, Grep, Glob
```

### Dangerous Combinations

**⚠️ Write + Bash**
Can create executables and run them.

**⚠️ Edit + Bash**
Can modify critical files (like .gitignore, package.json) and execute malicious commands.

**Mitigation:** Only grant these combinations to trusted subagents with clear, specific purposes.

## Testing Tool Access

### Verify Tool Grants

After creating a subagent, test that it has access to needed tools:

```markdown
> Use my-subagent to list all Python files
```

If subagent can't access a tool:
- Check the `tools` field
- Verify tool name is correct
- Use `/agents` to edit and add the tool

### Common Issues

**Issue:** Subagent says "I don't have access to..."

**Solutions:**
1. Check if `tools` field exists - remove it to inherit all
2. Add the specific tool name to the `tools` list
3. Verify tool name spelling (case-sensitive)

**Issue:** Subagent has too many capabilities

**Solutions:**
1. Add `tools` field with limited set
2. Explicitly list only necessary tools
3. Create separate subagents for different purposes

## Best Practices

### 1. Start Minimal

Begin with minimal tools, add more only when needed:

```markdown
# Start here
tools: Read, Grep, Glob

# Add if needed
tools: Read, Grep, Glob, Bash

# Add only if absolutely necessary
tools: Read, Edit, Bash, Grep, Glob
```

### 2. Match Tools to Purpose

**Read-only tasks:**
```markdown
tools: Read, Grep, Glob, Bash
```

**Modification tasks:**
```markdown
tools: Read, Edit, Bash, Grep, Glob
```

**Creation tasks:**
```markdown
tools: Read, Write, Bash, Grep, Glob
```

### 3. Document Tool Usage

In your system prompt, explain how to use each tool:

```markdown
You have access to the following tools:
- Read: Use to examine file contents before reviewing
- Grep: Use to search for security patterns like API keys
- Bash: Use to run `git diff` and see recent changes

When invoked:
1. Run `git diff` (Bash tool)
2. For each changed file, use Read to examine it
3. Use Grep to search for security issues
```

### 4. Consider Context

Some subagents need more tools in complex projects:

**Simple project:**
```markdown
tools: Read, Bash
```

**Large monorepo:**
```markdown
tools: Read, Bash, Grep, Glob
# Need Grep/Glob to navigate large codebase
```

## Quick Reference Table

| Tool | Read | Write | Modify | Execute | Risk | Common Use |
|------|------|-------|--------|---------|------|------------|
| **Read** | ✅ | ❌ | ❌ | ❌ | Low | Viewing files |
| **Write** | ❌ | ✅ | ❌ | ❌ | Medium | Creating files |
| **Edit** | ✅ | ❌ | ✅ | ❌ | High | Modifying files |
| **Bash** | ✅ | ✅ | ✅ | ✅ | High | Running commands |
| **Grep** | ✅ | ❌ | ❌ | ❌ | Low | Searching content |
| **Glob** | ✅ | ❌ | ❌ | ❌ | Low | Finding files |

## Summary

- **Default:** Omit `tools` to inherit all tools
- **Minimal:** Only grant tools the subagent truly needs
- **Security:** Be cautious with Edit and Bash
- **Testing:** Verify subagent has access to required tools
- **Iteration:** Add tools as needed based on real usage
