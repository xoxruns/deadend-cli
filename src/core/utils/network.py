import aiohttp


async def check_target_alive(target: str, timeout_seconds: float = 5.0) -> tuple[bool, int | None, str | None]:
    """
    Check whether a web target is reachable and responds to HTTP requests.

    Returns (alive, status_code, error_message).
    """
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            last_status: int | None = None
            last_error: str | None = None
            for method in ("HEAD", "GET"):
                try:
                    async with session.request(method, target, allow_redirects=True) as resp:
                        last_status = resp.status
                        if 200 <= resp.status < 400:
                            return True, resp.status, None
                except Exception as e:
                    last_error = str(e)
                    continue
            return False, last_status, last_error
    except Exception as e:
        return False, None, str(e)


