
# NEXSUS GPU Cycle Simulator v0.1
# Test: six independent execution paths
# All values are simulation assumptions, not hardware measurements.

PATHS = {
    "INT16-A": {"latency": 1, "interval": 1},
    "INT16-B": {"latency": 1, "interval": 1},
    "INT32":   {"latency": 1, "interval": 1},
    "FP16-A":  {"latency": 2, "interval": 1},
    "FP16-B":  {"latency": 2, "interval": 1},
    "FP32":    {"latency": 4, "interval": 1},
}

COMMANDS_PER_PATH = 8

events = {}
issued_total = 0
completed_total = 0
last_completion = 0

def record(cycle, kind, path, command_id):
    events.setdefault(cycle, {"issued": [], "completed": []})
    events[cycle][kind].append((path, command_id))

# Ideal mode: no register-port conflicts,
# no shared-resource conflicts, no dependencies.
for path, cfg in PATHS.items():
    latency = cfg["latency"]
    interval = cfg["interval"]

    for command_id in range(COMMANDS_PER_PATH):
        issue_cycle = command_id * interval
        completion_cycle = issue_cycle + latency

        record(issue_cycle, "issued", path, command_id)
        record(completion_cycle, "completed", path, command_id)

        last_completion = max(last_completion, completion_cycle)

print("Cycle | Issued this cycle | Completed total")
print("------+-------------------+----------------")

for cycle in range(last_completion + 1):
    e = events.get(cycle, {"issued": [], "completed": []})

    issued_total += len(e["issued"])
    completed_total += len(e["completed"])

    print(
        f"{cycle:5} |"
        f"{len(e['issued']):18} |"
        f"{completed_total:15}"
    )

expected = len(PATHS) * COMMANDS_PER_PATH

assert issued_total == expected
assert completed_total == expected

print("\nTotal commands:", issued_total)
print("Peak issue width:", len(PATHS), "commands/cycle")
print("Completion time:", last_completion, "cycles")
input("kapat")