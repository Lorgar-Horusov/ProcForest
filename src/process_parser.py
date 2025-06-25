import psutil


def get_parent_tree(proc: psutil.Process) -> dict:
    """
    Recursively retrieves the parent process tree for the given process.

    Args:
        proc (psutil.Process): The process whose parent tree is to be constructed.

    Returns:
        dict: A dictionary containing information about the parent process:
            - "ppid": Parent process ID (int)
            - "name": Parent process name (str)
            - "ppids": Nested dictionary with the parent's own parent information (recursive)
        Returns an empty dictionary if the process has no parent or if access is denied.

    Exceptions:
        psutil.NoSuchProcess: If the process no longer exists.
        psutil.AccessDenied: If access to process information is denied.
    """
    try:
        parent = proc.parent()
        if parent is None:
            return {}
        return {
            "ppid": parent.pid,
            "name": parent.name(),
            "ppids": get_parent_tree(parent),
            "memory": round(parent.memory_percent(), 2),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return {}


def compute_memory_with_children(pid, processes, children_map, memo, visited=None):
    if visited is None:
        visited = set()
    if pid in memo:
        return memo[pid]

    if pid in visited:
        return 0

    visited.add(pid)

    total = processes[pid]["memory"]
    for child_pid in children_map.get(pid, []):
        if child_pid in processes:
            total += compute_memory_with_children(
                child_pid, processes, children_map, memo, visited
            )

    visited.remove(pid)

    memo[pid] = round(total, 2)
    return memo[pid]


def list_process(filter=None) -> tuple:
    """
    Lists system processes, optionally filtered by process name or PID.
    For each matched process, includes its parent process tree.
    Args:
        filter (str or int, optional): If an integer or string representing a PID, filter for that PID.
                                       If a string, filter for processes with that name.
                                       If None, lists all processes.
    Returns:
        list: List of dictionaries, each with details about a process:
            - "pid": Process ID (int)
            - "name": Process name (str)
            - "username": process Owner (str)
            - "ppids": Parent process tree (dict, see get_parent_tree)
    """
    pid = None
    name = None
    if filter is not None:
        try:
            pid = int(filter)
        except ValueError:
            name = filter.lower()

    processes = {}
    children_map = {}

    for proc in psutil.process_iter(["pid", "ppid", "name", "username"]):
        try:
            info = proc.info
            proc_name = info["name"] or ""
            if pid is not None and info["pid"] != pid:
                continue
            if name is not None and proc_name.lower() != name:
                continue

            processes[info["pid"]] = {
                "pid": info["pid"],
                "ppid": info["ppid"],
                "name": proc_name,
                "username": (info["username"] or "unknown").split("\\")[-1],
                "memory": round(proc.memory_percent(), 2),
                "ppids": get_parent_tree(proc),
            }

            children_map.setdefault(info["ppid"], []).append(info["pid"])

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    memo = {}
    for pid in processes:
        processes[pid]["memory_total"] = compute_memory_with_children(
            pid, processes, children_map, memo
        )

    return processes, children_map


def text_sparkline(memory_percent: float):
    bars = "▁▂▃▄▅▆▇█"
    maximum = len(bars) - 1
    index = int(memory_percent * maximum / 100)
    return bars[index]


if __name__ == "__main__":
    import json

    print(json.dumps(list_process("librewolf.exe"), indent=4))
    # print(text_sparkline(50))
