# Blades of Brim: evidence and engineering implications

Research date: 2026-09-15. Game package: `com.sybogames.brim` ([Google Play](https://play.google.com/store/apps/details?id=com.sybogames.brim)).
The store reports an August 26, 2026 update; older guides cannot establish current
timings or a complete current taxonomy. Every rule below remains subject to
frame-level and device validation. Detection support is separate from research.

## Evidence levels

**Official**: developer documentation. **Community**: useful corroboration, potentially
outdated. **Hypothesis**: engineering interpretation requiring experiment.
Appearance descriptions from text are not visual annotation ground truth.

## Reference register

- [Supplied gameplay](https://www.youtube.com/watch?v=FPrG-8yTrBE): YouTube metadata
  identifies “Blades of Brim World Record Over 2.1 Billion Points NO CHEATS OR HACKS”,
  by foolish gamer. A high-score expert run is not a representative training corpus.
- [SYBO game page](https://sybogames.com/blades-of-brim/): wall-running, flight,
  portals, equipment, achievements and score progression.
- [Official help center](https://sybo.helpshift.com/hc/en/4-blades-of-brim/).
- [Community enemy taxonomy](https://bladesofbrim.fandom.com/wiki/Category:Enemies).
- [Independent controls guide](https://www.supersoluce.com/guide-tuto/blades-brim/bien-debuter-dans-blades-brim).

## Core loop and controls

Forward movement is automatic. Swipe left/right to traverse and side-strike,
up to jump/jump-attack, down on the ground to roll-attack, down in the air to
stomp. Swiping toward a wall can initiate wall-running. Double-tap summons a
pet when a whistle is available; tapping while mounted shoots. A single tap
can also activate an equipped weapon ability, so it is not a universal melee
attack button. Sources: controls guide above, [pet summoning](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/49-pets-summoning/),
[weapon ability example](https://bladesofbrim.fandom.com/wiki/Blade_of_Brim).

Jumping, rolling and lateral attacks have context-sensitive effects. A planner
must represent grounded/airborne/mounted/wall-running separately, confirm the
result of a gesture visually, and avoid treating issued input as successful
movement. Gesture durations and reaction windows must be measured, not inferred
from guide text. No universal forward “attack” command is justified.

## Enemy knowledge table

All entries require visual detection. Suggested methods are design decisions,
not claims of a trained detector. Priority 1 is lethal danger; 2 is safe path;
3 is threat mitigation; 4 is optional combat/progress.

| Mechanic | Appearance / state | Behavior and interaction | Priority / reaction | Perception method / evidence |
| --- | --- | --- | --- | --- |
| Goon | Small purple, one eye; biome colors vary | Strikes nearby runner; ordinary form takes one hit; roll, side or stomp attack | 3; attack only on safe geometry | Box + track + armor state; [official](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/31-goons/) |
| Armored Goon / Shielder | Shield, helmet and/or chest plate | Extra hits; armor is removed after strikes; knockback means a hit is not a kill | 3; preserve escape lane, reconfirm state | Same Goon family with visible armor state and unknown-hit-count fallback; [community](https://bladesofbrim.fandom.com/wiki/Shielder) |
| Flapper | Winged Goon, purple/magenta or biome colors | Flying; jump attack or aerial side movement; can swoop toward grounded player | 3; avoid blind jump with unsafe landing | Box + altitude / downward velocity; [community](https://bladesofbrim.fandom.com/wiki/Flapper) |
| Crusher / Crutheyr | Huge purple hammer enemy, helmet, large arms | Potential one-hit death; dodge hammer; requires additional strike | 1; evade committed strike before combat | Box + windup/locked-lane/recovery state; [official](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/27-crutheyrs/) and [community](https://bladesofbrim.fandom.com/wiki/Crusher) |
| Wizard | Robe, hat, staff, magic bubble | Flees, summons blockers; bubble and body require separate hits | 3; navigate summons first | Box + bubble state + track; [community](https://bladesofbrim.fandom.com/wiki/Wizard) |
| Fire / Arcane Wizard | World-dependent wizard variants | Fire version teleports and fires projectiles; arcane builds an obstacle sequence | 1 for projectile, 4 for pursuit | Wizard family + variant; detect projectiles independently; Wizard source above |
| Looter | Goon carrying treasure on back | Carries coins/essence; roll, side and stomp attacks work | 4; reward does not justify an unsafe move | Box + carried-loot attribute; [official](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/28-looters/) |
| Summoning crystal | Crystal enemy category; appearance needs visual confirmation | Listed separately by community; do not assume ordinary destructible crystal behavior | Unknown threat, conservative routing | Dedicated candidate class only after verified examples; [source](https://bladesofbrim.fandom.com/wiki/Summoning_crystal) |
| Captor with Brimling | Goon holding yellow furry creature | Rescue via defeat; community describes captor as stationary | 4, or mission reward after survival | Goon + captive attribute; [source](https://bladesofbrim.fandom.com/wiki/Brimling) |

Crutheyr and Crusher are **provisionally treated as aliases** because descriptions
align. This is an inference, not proof that no separate current enemy exists.
Do not train duplicate classes from the two names alone. Goon Lord is described
as a figurehead by the community taxonomy; do not invent a boss detector from
official promotional wording. Rare and newly introduced enemies remain unknown.

## Geometry and navigation

| Mechanic | Visual / behavior | Threat and interaction | Priority / reaction | Required perception |
| --- | --- | --- | --- | --- |
| Safe surface | Perspective paths, platforms; multiple heights | Lateral screen position alone does not imply a reachable lane | 2; require continuous swept route and landing | Semantic surface mask + plane / lane geometry |
| Gap / cliff / void | Missing surface and exposed edges | Falling can end a run | 1; use confirmed adjacent surface or feasible jump landing | Surface discontinuity + optical flow, not just a box |
| Wall / wall-run | Vertical structure beside route | Supports traversal in some contexts; head-on collision hazardous | 1/2; context-conditioned wall interaction | Wall mask + player altitude + temporal confirmation |
| Rock / solid barrier | Solid obstruction on path | Potential immediate run end | 1; evade with safe route | Box and nontraversable mask |
| Thorns / vegetation / pots | Low obstruction or breakable container | Collision damage; pots may hide behind effects | 3; distinguish breakable from lethal | Object/state classifier and track |
| Portal | Side-lane doorway | Changes world, visuals, and objective | 2 before optional entry; reset world assumptions | Portal box + scene-change detection |
| Projectile | Moving fireball or magical shot | Collision threat may cross lanes | 1/3; motion-based intercept estimate | Box/segmentation + velocity track |
| Special traversal | Flight, wall runs, broken elevated paths | Fixed three-lane ground logic is insufficient | 2; switch mode only on confirmed evidence | Temporal mode classifier and surface estimator |

Sources: [official game page](https://sybogames.com/blades-of-brim/),
[Cloud Kingdom](https://bladesofbrim.fandom.com/wiki/Cloud_Kingdom),
[portals](https://bladesofbrim.fandom.com/wiki/Portals).
Cloud Kingdom's documented landscape includes sandstone paths, wooden fences,
vines and broken elevated routes. World list includes Frozen Lakes, Magma Caverns,
Gloom Swamps, Thunder Reef, Twilight Peaks, Shattered Library and Crystal Canyons.
Exact boosters, balloons, bounce objects and launch objects are not established
by the inspected evidence; they remain research candidates, not implemented facts.

## Powerups

All are visually recognized pickups plus separately confirmed active states.
Duration varies with upgrades/equipment; never assume a fixed expiry from text.
The following is a compact summary of the [community powerup reference](https://bladesofbrim.fandom.com/wiki/Powerups).

| Name / appearance | Effect | Strategy / required reaction | Method |
| --- | --- | --- | --- |
| Magic Shield / purple shield | Damage protection and conditional revival | Prefer safe pickup; do not deliberately consume revival for coins | Pickup detection + shield visual state |
| Golden Wings / yellow wing | Coin attraction, slower falling, repeated aerial jumps, extended attack reach | Flight-capable planning only while confirmed active; preserve landing | Pickup + wings + temporal altitude |
| Poison Strike / green sword | One-strike defeat of enemies | Allows safer armored combat; does not remove gap risk | Pickup + weapon effect state |
| Midas Touch / blue fist | Converts enemies to gold and adds coin opportunities | Reclassify affected threats; still avoid obstructed path | Pickup + enemy material state |

An effect disappearing or a revival occurring invalidates cached buffs.
Uncertain active-state recognition must never relax a survival constraint.

## Pets

Official [summoning](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/49-pets-summoning/)
and [abilities](https://sybo.helpshift.com/hc/en/4-blades-of-brim/faq/47-pets-abilities/)
establish whistles, double-tap activation, variable duration, projectile attacks,
coin attraction, extra jump and sacrifice on fatal damage. Dragons support flight
through upward swipes. Community lists wolves, horses, goats, boars and dragons;
element types change shot patterns. Exact duration and selected pet must be
inferred from visible state, not guessed from silhouette alone.

Perception: whistle/HUD availability, mounted player, pet type, timer if readable,
and disappearance. Strategic policy: preserve the whistle during easy safe
running; summon when a verified dangerous section, low health or a safe pet
objective makes its defensive value exceed saving it. A summon cannot replace
an immediate dodge if activation would arrive too late. Shooting requires a
confirmed mounted state and a useful target. Pet availability alone is insufficient.

## Resources and objectives

Coins buy upgrades and equipment; essence is a rarer progression/revive resource.
Looters and pots may carry rewards. Brimling rescue supports daily quests.
Portal quests have in-portal deadlines and may reward a vault chest. Long-term
achievements, current level goals and temporary portal objectives are distinct.
Sources: [coins](https://bladesofbrim.fandom.com/wiki/Coins),
[Brimlings](https://bladesofbrim.fandom.com/wiki/Brimling),
[portals](https://bladesofbrim.fandom.com/wiki/Portals),
[achievements](https://bladesofbrim.fandom.com/wiki/Achievements).

Perception: UI-region OCR with repeated identical reads and icon agreement.
Unknown goal text remains unknown, with no fabricated progress. Planning ranks
survival, path, forced traversal and threats above combat, objectives, powerups,
essence and coins. Inventory purchases and paid revives are outside gameplay
control. Exact achievement thresholds differ between older sources; no static
threshold is treated as current truth.

## Unresolved evidence needed before release

- Visually audited enemy/armor taxonomy across worlds, player skins and effects.
- Ground truth for safe surfaces, gaps, landing feasibility and player lane.
- Timing distribution for every gesture and context, including device latency.
- Menu/loading/pause/death labels and negative screens.
- UI localization, pet availability, powerup expiry and mission OCR accuracy.
- Closed-loop survival on a real Android device. Video replay cannot establish it.
