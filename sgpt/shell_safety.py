import re
from dataclasses import dataclass
from typing import Pattern

import typer


@dataclass(frozen=True)
class ShellSafetyIssue:
    severity: str
    title: str
    detail: str


@dataclass(frozen=True)
class ShellSafetyRule:
    severity: str
    title: str
    detail: str
    pattern: Pattern[str]


@dataclass(frozen=True)
class ShellSafetyReport:
    command: str
    issues: tuple[ShellSafetyIssue, ...]

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def is_high_risk(self) -> bool:
        return any(issue.severity == "high" for issue in self.issues)

    @property
    def requires_confirmation(self) -> bool:
        return self.is_high_risk


def _compile(pattern: str) -> Pattern[str]:
    return re.compile(pattern, flags=re.IGNORECASE)


RULES: tuple[ShellSafetyRule, ...] = (
    ShellSafetyRule(
        severity="high",
        title="Destructive deletion",
        detail="Detected recursive or forced deletion that can irreversibly remove files.",
        pattern=_compile(r"\brm\s+-[^\n;&|]*(?:r[^\n;&|]*f|f[^\n;&|]*r)[^\n;&|]*\b"),
    ),
    ShellSafetyRule(
        severity="high",
        title="Destructive deletion",
        detail="Detected Windows or PowerShell deletion with recursive or force options.",
        pattern=_compile(
            r"\b(?:remove-item|del|erase)\b[^\n;&|]*(?:-recurse|-force|/s|/q)"
        ),
    ),
    ShellSafetyRule(
        severity="high",
        title="Disk or filesystem operation",
        detail="Detected a disk, partition, or filesystem command that can damage the system or erase data.",
        pattern=_compile(r"\b(?:mkfs(?:\.\w+)?|dd|fdisk|parted|diskpart|format(?:\.com)?)\b"),
    ),
    ShellSafetyRule(
        severity="high",
        title="Remote script execution",
        detail="Detected a command that downloads content from the network and pipes it directly to a shell.",
        pattern=_compile(
            r"\b(?:curl|wget)\b[^\n]*\|\s*(?:bash|sh|zsh)\b|\b(?:invoke-webrequest|iwr)\b[^\n]*\|\s*(?:iex|powershell|pwsh)\b"
        ),
    ),
    ShellSafetyRule(
        severity="high",
        title="System shutdown or reboot",
        detail="Detected a command that shuts down or restarts the system.",
        pattern=_compile(r"\b(?:shutdown|reboot|poweroff|halt)\b|\binit\s+[06]\b"),
    ),
    ShellSafetyRule(
        severity="high",
        title="Account removal",
        detail="Detected a user or account deletion command.",
        pattern=_compile(r"\b(?:userdel|deluser)\b|\bnet\s+user\s+\S+\s+/delete\b"),
    ),
    ShellSafetyRule(
        severity="medium",
        title="Recursive permission change",
        detail="Detected a recursive ownership or permission change. Review the target path carefully before execution.",
        pattern=_compile(r"\b(?:chmod|chown)\b[^\n;&|]*(?:-R|--recursive)\b"),
    ),
    ShellSafetyRule(
        severity="medium",
        title="Sensitive file overwrite",
        detail="Detected redirection into a sensitive system path.",
        pattern=_compile(
            r"(?:^|[;&|])\s*(?:sudo\s+)?(?:tee|cat|echo)\b[^\n]*?(?:>>?|1>>?)\s*/(?:etc|usr|boot|var)/(?!tmp\b)"
        ),
    ),
)


def analyze_shell_command(command: str) -> ShellSafetyReport:
    normalized_command = " ".join(command.split())
    issues = []
    for rule in RULES:
        if rule.pattern.search(normalized_command):
            issues.append(
                ShellSafetyIssue(
                    severity=rule.severity,
                    title=rule.title,
                    detail=rule.detail,
                )
            )
    return ShellSafetyReport(command=normalized_command or command, issues=tuple(issues))


def get_shell_safety_lines(report: ShellSafetyReport) -> tuple[str, ...]:
    if not report.has_issues:
        return ()
    headline = (
        "Shell safety check: HIGH RISK command detected."
        if report.is_high_risk
        else "Shell safety check: review recommended."
    )
    details = tuple(
        f"[{issue.severity.upper()}] {issue.title}: {issue.detail}"
        for issue in report.issues
    )
    return (headline, *details)


def display_shell_safety_report(report: ShellSafetyReport) -> None:
    if not report.has_issues:
        return
    color = "red" if report.is_high_risk else "yellow"
    for line in get_shell_safety_lines(report):
        typer.secho(line, fg=color)


def confirm_shell_execution(report: ShellSafetyReport) -> bool:
    if not report.requires_confirmation:
        return True
    return typer.confirm(
        "High-risk command detected. Execute this command anyway?",
        default=False,
    )


def blocked_shell_execution_message(report: ShellSafetyReport) -> str:
    lines = [
        "Blocked high-risk shell command by ShellGPT safety check.",
        f"Command: {report.command}",
    ]
    lines.extend(f"- {issue.title}: {issue.detail}" for issue in report.issues)
    return "\n".join(lines)
