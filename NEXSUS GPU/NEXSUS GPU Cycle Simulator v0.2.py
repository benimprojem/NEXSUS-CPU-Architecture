
# NEXSUS GPU Group-8 — Ideal independent-command test
# Assumptions, not measured hardware characteristics.

LINES = 8
COMMANDS_PER_PATH = 8

PATHS = {
    "INT16-A": 1,
    "INT16-B": 1,
    "INT32":   1,
    "FP16-A":  2,
    "FP16-B":  2,
    "FP32":    4,
}

events = {}
total_issued = 0
total_completed = 0

def add_event(cycle, kind, path, line, command):
    if cycle not in events:
        events[cycle] = {"issue": [], "complete": []}
    events[cycle][kind].append((line, path, command))

# Every Line has six independent paths.
for line in range(LINES):
    for path, latency in PATHS.items():
        for command in range(COMMANDS_PER_PATH):
            issue_cycle = command
            completion_cycle = issue_cycle + latency

            add_event(issue_cycle, "issue", path, line, command)
            add_event(completion_cycle, "complete", path, line, command)

last_cycle = max(events)

print("Cycle | Issued | Completed this cycle | Completed total")
print("------+--------+----------------------+----------------")

for cycle in range(last_cycle + 1):
    current = events.get(
        cycle, {"issue": [], "complete": []}
    )

    issued = len(current["issue"])
    completed = len(current["complete"])

    total_issued += issued
    total_completed += completed

    print(
        f"{cycle:5} | {issued:6} |"
        f" {completed:20} | {total_completed:14}"
    )

expected = LINES * len(PATHS) * COMMANDS_PER_PATH

assert total_issued == expected == 384
assert total_completed == expected == 384

print("\nTotal commands:", total_issued)
print("Peak issue width:", LINES * len(PATHS))
print("Final completion cycle:", last_cycle)
input("kapat")