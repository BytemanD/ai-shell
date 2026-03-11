import os
import platform
import subprocess
from typing import Optional

import click
from openai import OpenAI
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    shell: Optional[str] = None

    class Config:
        env_prefix = "OPENAI_"


def get_shell() -> str:
    system = platform.system()
    if system == "Windows":
        return "powershell"
    return "bash"


def get_working_directory() -> str:
    return os.getcwd()


def execute_command(command: str, shell: str) -> tuple[int, str, str]:
    if platform.system() == "Windows":
        cmd = ["powershell", "-Command", command]
    else:
        cmd = ["bash", "-c", command]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=get_working_directory()
    )
    return result.returncode, result.stdout, result.stderr


def get_ai_response(client: OpenAI, user_input: str, shell: str, model: str) -> str:
    system_prompt = f"""You are a CLI assistant that generates commands for the user.
The current working directory is: {get_working_directory()}
The current shell is: {shell}

Based on the user's request, generate the appropriate command to execute.
Output ONLY the command itself, without any explanation or markdown formatting.
If the request cannot be fulfilled with a command, output exactly "NO_COMMAND" """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        max_tokens=500,
    )

    return response.choices[0].message.content.strip()


def interactive_loop(client: OpenAI, shell: str, model: str):
    click.echo(f"\n{'=' * 50}")
    click.echo(f"  AI Shell - Interactive Mode (type 'exit' to quit)")
    click.echo(f"  Shell: {shell} | Model: {model} | CWD: {get_working_directory()}")
    click.echo(f"{'=' * 50}\n")

    while True:
        try:
            prompt = click.prompt(f"\n[{shell}] > ", prompt_suffix="")
            if prompt.lower() in ("exit", "quit", "q"):
                click.echo("Goodbye!")
                break

            if not prompt.strip():
                continue

            command = get_ai_response(client, prompt, shell, model)

            if command == "NO_COMMAND":
                click.echo("The AI could not generate a command for your request.")
                continue

            click.echo(f"\n  Command: {click.style(command, fg='cyan')}\n")

            confirm = click.confirm("Execute?", default=True)
            if not confirm:
                continue

            returncode, stdout, stderr = execute_command(command, shell)

            if stdout:
                click.echo(stdout)
            if stderr:
                click.echo(click.style(stderr, fg="yellow"), err=True)

            fg = "green" if returncode == 0 else "red"
            click.echo(click.style(f"\nExit code: {returncode}", fg=fg))

        except KeyboardInterrupt:
            click.echo("\nGoodbye!")
            break
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg="red"), err=True)


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "--shell",
    "-s",
    type=click.Choice(["bash", "powershell"]),
    default=None,
    help="Force a specific shell (bash or powershell)",
)
@click.option("--dry-run", is_flag=True, help="Show the command without executing it")
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
@click.option(
    "--base-url",
    envvar="OPENAI_BASE_URL",
    default=None,
    help="OpenAI API base URL",
)
@click.option(
    "--model",
    envvar="OPENAI_MODEL",
    default=None,
    help="OpenAI model to use",
)
@click.option("--no-exec", is_flag=True, help="Just show the command, don't execute")
def main(
    prompt: Optional[str],
    shell: Optional[str],
    dry_run: bool,
    api_key: Optional[str],
    base_url: Optional[str],
    model: Optional[str],
    no_exec: bool,
):
    """AI Shell - Generate and execute shell commands using AI"""

    config = Config(
        api_key=api_key or "",
        base_url=base_url or "",
        model=model or "",
        shell=shell,
    )

    if not config.api_key:
        click.echo(
            "Error: Please provide an API key via --api-key or OPENAI_API_KEY environment variable",
            err=True,
        )
        raise click.Abort()

    client = OpenAI(api_key=config.api_key, base_url=config.base_url or None)

    if config.shell is None:
        config.shell = get_shell()

    if not prompt:
        interactive_loop(client, config.shell, config.model)
        return

    click.echo(f"[Using {config.shell} shell, model: {config.model}]")

    try:
        command = get_ai_response(client, prompt, config.shell, config.model)
    except Exception as e:
        click.echo(f"Error getting AI response: {e}", err=True)
        raise click.Abort()

    if command == "NO_COMMAND":
        click.echo("The AI could not generate a command for your request.")
        return

    click.echo(f"\nGenerated command: {command}\n")

    if no_exec or dry_run:
        return

    click.echo(f"Executing...\n{'-' * 40}")

    returncode, stdout, stderr = execute_command(command, config.shell)

    if stdout:
        click.echo(stdout)
    if stderr:
        click.echo(stderr, err=True)

    click.echo(f"\n{'-' * 40}\nExit code: {returncode}")


if __name__ == "__main__":
    main()
