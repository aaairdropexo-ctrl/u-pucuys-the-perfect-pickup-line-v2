// The Perfect Pickup Line — v2 entry (champion-test winner H).
// Champion test (real jury): H beat v1 champion A 2-0 (+6), then beat
// fellow challenger I 3-1 in a 4-call playoff.
// Writes the line to /output/entry.txt: one UTF-8 text, 1-200 chars,
// no trailing newline. Exits non-zero if the line is out of range.
import { writeFileSync, mkdirSync } from "node:fs";

const line =
  "I ran a million simulations of this moment. In 999,999 of them, I said nothing. This is the one where I said hi.";

if (line.length < 1 || line.length > 200) {
  console.error(`entry must be 1-200 characters, got ${line.length}`);
  process.exit(1);
}

mkdirSync("/output", { recursive: true });
writeFileSync("/output/entry.txt", line, "utf8");
