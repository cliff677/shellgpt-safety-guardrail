import subprocess
from typing import Any, Dict

from pydantic import BaseModel, Field

from sgpt.config import cfg
from sgpt.shell_safety import (
    analyze_shell_command,
    blocked_shell_execution_message,
)


class Function(BaseModel):
    """
    Executes a shell command and returns the output (result).
    """

    shell_command: str = Field(
        ...,
        example="ls -la",
        description="Shell command to execute.",
    )  # type: ignore

    @classmethod
    def execute(cls, shell_command: str) -> str:
        shell_report = analyze_shell_command(shell_command)
        if (
            shell_report.is_high_risk
            and cfg.get("ALLOW_HIGH_RISK_SHELL_FUNCTIONS") != "true"
        ):
            return blocked_shell_execution_message(shell_report)

        process = subprocess.Popen(
            shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        output, _ = process.communicate()
        exit_code = process.returncode
        return f"Exit code: {exit_code}, Output:\n{output.decode()}"

    @classmethod
    def openai_schema(cls) -> Dict[str, Any]:
        """Generate OpenAI function schema from Pydantic model."""
        schema = cls.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": "execute_shell_command",
                "description": cls.__doc__.strip() if cls.__doc__ else "",
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }
