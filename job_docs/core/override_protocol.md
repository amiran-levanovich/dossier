# User-Directed Overrides — the escape hatch

The no-fabrication rule binds **the agents, not the user**. If the user explicitly asks to include something the KB cannot back ("just add Kafka to this one"), do not fight them:

1. **Warn once, concretely.** One short paragraph: what an interviewer or background check could probe, and the honest alternative (e.g. `"Kafka — actively ramping"`). No moralizing, no second warning later.
2. **Confirm** via AskUserQuestion — proceed / use the honest alternative / drop it.
3. **Get details.** If they proceed, briefly interview for what to claim (role, depth, wording) so it is coherent and defensible live.
4. **Record.** Write the claim to `applications/<company>/overrides.md`, marked `user-directed`, with date and scope. **It never enters `knowledge/`** — the KB stays true; the override is per-application.

Trace entries may then point at `overrides.md`. The verifier treats override-sourced claims as sourced and reports them as a single INFO line (`N user-directed claims present`) — never as findings. Agents never volunteer an override, never extend one beyond what the user specified, and never carry one silently into a different application. Overrides never touch the master CV (`lifecycle/master_documents.md`) — the master holds only KB-backed content.
