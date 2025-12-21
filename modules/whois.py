import subprocess


def run(target: str) -> str:
    """
    Run WHOIS lookup for the given target.

    Returns:
        WHOIS output as string
    """

    if not target:
        raise ValueError("Target is empty")

    try:
        result = subprocess.check_output(
            ["whois", target],
            stderr=subprocess.STDOUT,
            text=True
        )
        return result

    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output)
