#!/usr/bin/env python3
"""
AI-Generated Code Security Scanner
OneZero Bank — AI SDLC Security Gate

Scans code written/edited by AI coding tools (Claude Code, Codex, Copilot)
for common security vulnerabilities before commit.

Triggered as a PostToolUse hook after Write/Edit tool calls.
"""

import sys
import json
import re
import os
from pathlib import Path

# ── Vulnerability patterns ────────────────────────────────────────────────────

RULES = [
    # Secrets / Credentials
    {
        "id": "HARDCODED_SECRET",
        "severity": "CRITICAL",
        "description": "Hardcoded secret or credential detected",
        "pattern": re.compile(
            r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth_token'
            r'|access_key|private_key|client_secret)\s*=\s*["\'][^"\']{6,}["\']'
        ),
    },
    {
        "id": "AWS_KEY",
        "severity": "CRITICAL",
        "description": "AWS Access Key ID pattern detected",
        "pattern": re.compile(r'AKIA[0-9A-Z]{16}'),
    },
    {
        "id": "GENERIC_SECRET_ASSIGN",
        "severity": "HIGH",
        "description": "Potential secret in variable assignment",
        "pattern": re.compile(
            r'(?i)(SECRET|TOKEN|KEY|PASSWORD)\s*=\s*["\'][A-Za-z0-9+/=_\-]{16,}["\']'
        ),
    },

    # Prompt Injection (AI-specific)
    {
        "id": "PROMPT_INJECTION_RISK",
        "severity": "HIGH",
        "description": "User input passed directly into prompt without sanitization",
        "pattern": re.compile(
            r'(?i)(f["\'].*\{(user_input|user_message|query|user_query|request)\}|'
            r'prompt\s*[+]=?\s*(user_input|user_message|query|request)|'
            r'messages\.append.*\{.*user_input.*\})'
        ),
    },
    {
        "id": "SYSTEM_PROMPT_OVERRIDE_RISK",
        "severity": "HIGH",
        "description": "System prompt constructed from external input — injection risk",
        "pattern": re.compile(
            r'(?i)system.*prompt.*=.*\+|system.*=.*f["\'].*\{(user|input|data|request)'
        ),
    },
    {
        "id": "RAG_INJECTION_RISK",
        "severity": "HIGH",
        "description": "RAG retrieved content inserted into prompt without sanitization",
        "pattern": re.compile(
            r'(?i)(context|retrieved|chunks|documents)\s*=.*retriev|'
            r'prompt.*\+.*context|f["\'].*\{context\}.*["\']'
        ),
    },

    # SQL Injection
    {
        "id": "SQL_INJECTION",
        "severity": "CRITICAL",
        "description": "SQL query built with string concatenation — injection risk",
        "pattern": re.compile(
            r'(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE).*(\+|%s|\.format\(|f["\'])'
            r'.*WHERE|'
            r'(?i)execute\s*\(\s*["\'].*\+|'
            r'(?i)cursor\.execute\s*\(\s*f["\']'
        ),
    },

    # Command Injection
    {
        "id": "COMMAND_INJECTION",
        "severity": "CRITICAL",
        "description": "Shell command execution with unsanitized input",
        "pattern": re.compile(
            r'(?i)(os\.system|subprocess\.call|subprocess\.run|popen)\s*\('
            r'\s*["\'].*\+|'
            r'(?i)(os\.system|subprocess\.(call|run|Popen))\s*\(\s*f["\']'
        ),
    },
    {
        "id": "SHELL_TRUE",
        "severity": "HIGH",
        "description": "subprocess called with shell=True — potential injection risk",
        "pattern": re.compile(r'subprocess\.(run|call|Popen).*shell\s*=\s*True'),
    },

    # Path Traversal
    {
        "id": "PATH_TRAVERSAL",
        "severity": "HIGH",
        "description": "File path constructed from user input — traversal risk",
        "pattern": re.compile(
            r'(?i)(open|os\.path\.join|pathlib\.Path)\s*\(\s*'
            r'(user_input|request\.|params\.|query\.|data\.|filename)'
        ),
    },

    # XSS
    {
        "id": "XSS_RISK",
        "severity": "HIGH",
        "description": "Unescaped user content rendered in HTML — XSS risk",
        "pattern": re.compile(
            r'(?i)(render_template_string|Markup\(|mark_safe\(|innerHTML\s*=)'
            r'\s*.*\+|(innerHTML|outerHTML|document\.write)\s*=\s*\w'
        ),
    },

    # SSRF
    {
        "id": "SSRF_RISK",
        "severity": "HIGH",
        "description": "HTTP request made to user-controlled URL — SSRF risk",
        "pattern": re.compile(
            r'(?i)(requests\.(get|post|put|delete|head)|httpx\.(get|post)|'
            r'urllib\.request\.urlopen)\s*\(\s*(user_input|request\.|url\s*=\s*request)'
        ),
    },

    # Insecure Deserialization
    {
        "id": "INSECURE_DESERIALIZATION",
        "severity": "CRITICAL",
        "description": "pickle.loads on untrusted data — arbitrary code execution risk",
        "pattern": re.compile(r'pickle\.loads?\s*\('),
    },
    {
        "id": "YAML_UNSAFE_LOAD",
        "severity": "HIGH",
        "description": "yaml.load without Loader — use yaml.safe_load instead",
        "pattern": re.compile(r'yaml\.load\s*\([^)]*\)(?!\s*#.*safe)'),
    },

    # Weak Cryptography
    {
        "id": "WEAK_HASH",
        "severity": "HIGH",
        "description": "MD5 or SHA1 used — insecure for security purposes",
        "pattern": re.compile(r'(?i)(hashlib\.(md5|sha1)|MD5\(|SHA1\()'),
    },
    {
        "id": "WEAK_RANDOM",
        "severity": "HIGH",
        "description": "random module used for security — use secrets module instead",
        "pattern": re.compile(
            r'(?i)random\.(random|randint|choice|token)\s*\('
            r'(?!.*#.*not.security)'
        ),
    },

    # Debug / Insecure Config
    {
        "id": "DEBUG_ENABLED",
        "severity": "MEDIUM",
        "description": "Debug mode enabled — must not be in production",
        "pattern": re.compile(r'(?i)(DEBUG\s*=\s*True|app\.run\s*\(.*debug\s*=\s*True)'),
    },
    {
        "id": "CORS_WILDCARD",
        "severity": "MEDIUM",
        "description": "CORS wildcard (*) allows any origin",
        "pattern": re.compile(r'(?i)(CORS_ORIGIN|Access-Control-Allow-Origin)["\s]*[=:]["\s]*["\']?\*'),
    },

    # LLM Tool Use
    {
        "id": "UNVALIDATED_TOOL_OUTPUT",
        "severity": "HIGH",
        "description": "LLM tool output used directly without validation — tool poisoning risk",
        "pattern": re.compile(
            r'(?i)(tool_result|tool_output|function_result)\s*='
            r'.*\n.*exec\(|eval\(.*tool'
        ),
    },
    {
        "id": "EVAL_USAGE",
        "severity": "CRITICAL",
        "description": "eval() or exec() with dynamic input — code injection risk",
        "pattern": re.compile(r'(?i)\b(eval|exec)\s*\(\s*(?![\"\'])[^)]+\)'),
    },
]

# ── Severity ordering ─────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
SEVERITY_COLOR = {
    "CRITICAL": "\033[91m",  # red
    "HIGH":     "\033[93m",  # yellow
    "MEDIUM":   "\033[94m",  # blue
    "LOW":      "\033[37m",  # gray
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def scan_content(content: str, filename: str) -> list[dict]:
    findings = []
    lines = content.splitlines()
    for line_no, line in enumerate(lines, start=1):
        # Skip obvious comments
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        for rule in RULES:
            if rule["pattern"].search(line):
                findings.append({
                    "rule_id":     rule["id"],
                    "severity":    rule["severity"],
                    "description": rule["description"],
                    "file":        filename,
                    "line":        line_no,
                    "snippet":     line.strip()[:120],
                })
    return findings


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return f"{BOLD}\033[92m✓ AI Security Gate: No issues detected{RESET}\n"

    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 9))
    critical = [f for f in findings if f["severity"] == "CRITICAL"]
    high     = [f for f in findings if f["severity"] == "HIGH"]
    other    = [f for f in findings if f["severity"] not in ("CRITICAL", "HIGH")]

    lines = [
        f"\n{BOLD}{'='*60}",
        f"  AI Security Gate — OneZero Bank AI SDLC",
        f"{'='*60}{RESET}",
        f"  Found {len(findings)} issue(s): "
        f"{SEVERITY_COLOR['CRITICAL']}{len(critical)} CRITICAL{RESET}  "
        f"{SEVERITY_COLOR['HIGH']}{len(high)} HIGH{RESET}  "
        f"{len(other)} other",
        "",
    ]

    for f in findings:
        color = SEVERITY_COLOR.get(f["severity"], "")
        lines += [
            f"  {color}{BOLD}[{f['severity']}]{RESET} {f['rule_id']}",
            f"  {f['description']}",
            f"  {BOLD}Location:{RESET} {f['file']}:{f['line']}",
            f"  {BOLD}Code:{RESET} {f['snippet']}",
            "",
        ]

    lines += [
        f"{BOLD}{'='*60}{RESET}",
        f"  Fix CRITICAL and HIGH issues before committing AI-generated code.",
        f"  Run `/secure-review` in Claude Code for remediation guidance.",
        f"{BOLD}{'='*60}{RESET}\n",
    ]
    return "\n".join(lines)


def main():
    """
    Called by Claude Code PostToolUse hook.
    Reads hook payload from stdin (JSON).
    """
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # Not called with proper hook payload — run as CLI on file arg
        if len(sys.argv) > 1:
            path = sys.argv[1]
            try:
                content = Path(path).read_text(encoding="utf-8", errors="ignore")
                findings = scan_content(content, path)
                print(format_findings(findings))
                sys.exit(1 if any(f["severity"] in ("CRITICAL", "HIGH") for f in findings) else 0)
            except FileNotFoundError:
                print(f"File not found: {path}", file=sys.stderr)
                sys.exit(1)
        sys.exit(0)

    # Extract file path from hook payload
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Only scan source code files
    scannable_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
        ".rb", ".php", ".cs", ".cpp", ".c", ".rs", ".kt", ".swift",
    }
    if Path(file_path).suffix.lower() not in scannable_extensions:
        sys.exit(0)

    # Get content: prefer new_string from Edit, otherwise read file
    content = tool_input.get("new_string", "")
    if not content and os.path.exists(file_path):
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            sys.exit(0)

    if not content:
        sys.exit(0)

    findings = scan_content(content, file_path)
    output = format_findings(findings)

    # Print to stderr so Claude Code surfaces it as a warning
    print(output, file=sys.stderr)

    # Exit 2 = non-blocking warning (Claude sees it but continues)
    # Change to exit(1) to BLOCK the action on CRITICAL findings
    has_critical = any(f["severity"] == "CRITICAL" for f in findings)
    sys.exit(2 if findings else 0)  # 2 = show warning, don't block


if __name__ == "__main__":
    main()
