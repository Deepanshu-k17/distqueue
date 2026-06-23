import time


_attempt_memory = {}


def sleep_task(payload: dict):
    seconds = payload.get("seconds", 1)
    time.sleep(seconds)
    return {
        "message": f"Slept for {seconds} seconds"
    }


def echo_task(payload: dict):
    return {
        "echo": payload
    }


def fail_task(payload: dict):
    raise RuntimeError("Intentional failure from fail_task")


def unstable_task(payload: dict):
    """
    Fails first N times, then succeeds.
    Example payload:
    {
      "job_key": "test_retry_1",
      "fail_times": 2
    }
    """
    job_key = payload.get("job_key", "default")
    fail_times = payload.get("fail_times", 1)

    current_attempts = _attempt_memory.get(job_key, 0)

    if current_attempts < fail_times:
        _attempt_memory[job_key] = current_attempts + 1
        raise RuntimeError(
            f"unstable_task failed attempt {current_attempts + 1}/{fail_times}"
        )

    return {
        "message": "unstable_task succeeded",
        "failed_before_success": fail_times
    }


def execute_task(task_type: str, payload: dict):
    if task_type == "sleep_task":
        return sleep_task(payload)

    if task_type == "echo_task":
        return echo_task(payload)

    if task_type == "fail_task":
        return fail_task(payload)

    if task_type == "unstable_task":
        return unstable_task(payload)

    raise ValueError(f"Unknown task_type: {task_type}")