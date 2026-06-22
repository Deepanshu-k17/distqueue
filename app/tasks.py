import time


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


def execute_task(task_type: str, payload: dict):
    if task_type == "sleep_task":
        return sleep_task(payload)

    if task_type == "echo_task":
        return echo_task(payload)

    if task_type == "fail_task":
        return fail_task(payload)

    raise ValueError(f"Unknown task_type: {task_type}")