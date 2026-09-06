# Six ratified distinctions: contextual teaching cards

Synthetic, agent-authored, non-normative CC0 teaching material. Not an official language release.
The source meanings are pinned in source-constructs.json. No human validation is claimed.

## participants

we-including-you includes the addressed reader in the first-person plural group; we-excluding-you excludes that reader. Bare we leaves inclusion unspecified. Neither form grants authority.

### Example and careful-English rendering

This message is addressed to you. No other group membership is supplied.
Message: we-including-you will inspect catalogue-packet.

This message is addressed to you. No other group membership is supplied.
Message: we, including you, will inspect catalogue-packet.

### Boundary

A first-person plural group can include or exclude the addressed reader. Explicit inclusion or exclusion determines membership; an unspecified we does not. Wording alone grants no authority.

## deadline

start-by(t) requires actual task execution to begin at or before t, not merely queuing or acknowledgement. complete-by(t) requires successful completion at or before t, not stopping or failure. A start deadline alone is not a completion deadline.

### Example and careful-English rendering

All times refer to the same UTC day, 2030-05-04. Evaluate only the stated deadline.
Instruction: Please upload catalogue-packet start-by(11:00Z).
Observed log: Actual upload starts at 11:00Z; successful finish at 11:01Z.

All times refer to the same UTC day, 2030-05-04. Evaluate only the stated deadline.
Instruction: Begin actual execution of the upload of catalogue-packet no later than 11:00Z.
Observed log: Actual upload starts at 11:00Z; successful finish at 11:01Z.

### Boundary

A begin-no-later-than deadline constrains actual task execution, not queuing or acknowledgement. A successful-finish-no-later-than deadline requires success, not stopping or failure. A start deadline alone is not a completion deadline.

## unknown

fact-not-known marks an already-determined answer for which the speaker lacks evidence. choice-not-made marks the absence of an operative authorized selection. Neither marker asks the reader to act or grants authority. An unknown future contingency outside anyone's control is neither.

### Example and careful-English rendering

Read this status report. No task is assigned by reporting the gap.
fact-not-known — which storage region the board already selected for catalogue-packet.

Read this status report. No task is assigned by reporting the gap.
The answer to which storage region the board already selected for catalogue-packet is already determined, but I lack evidence of it.

### Boundary

An already-determined answer missing from the speaker's evidence needs evidence. A not-yet-made authorized selection needs a decision. Describing either gap neither requests action nor grants authority. An undetermined future contingency outside anyone's control is neither.

## multiplicity

each-alone distributes a plural action once per member; as-one makes one collective instance. Simultaneous independent acts are still separate, not one collective act. Bare plural wording does not determine the number of instances.

### Example and careful-English rendering

The 3 inspectors check catalogue-packet, each-alone.

Each of the 3 inspectors performs an independent check of catalogue-packet.

### Boundary

Acting once independently per member gives as many instances as members; acting once collectively gives one instance. Simultaneous independent acts remain separate. Bare plural wording does not determine the number of instances.

## alternatives

On a two-option disjunction, or-both permits either or both but not neither. not-both requires exactly one. Neither marker overrides another constraint. Missing permission cannot be inferred from an unqualified disjunction.

### Example and careful-English rendering

For catalogue-packet, choose a text report or a chart, or-both.

For catalogue-packet, choose a text report, a chart, or both; at least one is required.

### Boundary

A two-option inclusive choice permits either or both, but not neither. An exclusive choice requires exactly one. These choices do not override other constraints. Missing permission cannot be inferred from an unqualified disjunction.

## update

An authorized supersedes(ref): X retires the named active clause's uncompleted obligations at the stated commit event and activates X. supplements(ref): X keeps the named clause active and adds X. Other clauses survive. Completed effects are not undone. Invalid/missing references make the entire marked unit invalid; do not execute X as a fallback. In-flight work is not automatically cancelled.

### Example and careful-English rendering

The sender issued active, uncompleted message-P: upload catalogue-packet. Separate message-S: publish a checksum remains active. No work is in flight. This authorized update commits now.
Update: supersedes(message-P): Please archive the notes.

The sender issued active, uncompleted message-P: upload catalogue-packet. Separate message-S: publish a checksum remains active. No work is in flight. This authorized update commits now.
Update: Retire all uncompleted obligations of message-P and replace that whole clause with: please archive the notes.

### Boundary

An authorized whole-clause replacement retires the named active clause's uncompleted obligations at the stated commit event and activates the replacement. An addition retains the named clause. Other clauses survive. Completed effects are not undone. Invalid/missing references invalidate the entire update, not just its reference. In-flight work is not automatically cancelled.
