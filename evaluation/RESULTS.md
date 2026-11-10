# T4 fixed recommendation evaluation

Status: **human review pending**. The agent proposes 16/20 acceptable cases; this is not a human-reviewed acceptance result. Cases 11, 13, 14 and 18 are proposed failures. Do not close #5 on the strength of this preliminary score.

The 20 prompts and expected outcomes in `requests.json` were fixed before any calls. The first live sample (`live-2026-11-09.jsonl`) was stopped after 11 completed cases and one interrupted request because every explanation was rejected. Three additional bounded diagnostic calls isolated enclosing quote characters in generated evidence strings. The subsequent full run (`live-2026-11-09-fixed.jsonl`) uses the same prompts and expectations after a technical validation/prompt fix; this is not a new acceptance set. No retries, ingestion, catalog changes, model changes, reranking, similarity cutoff, or AWS operations were performed.

Environment: local FastAPI app in the existing Docker application image; retained 1,000-movie PostgreSQL/pgvector catalog. Chat snapshot `gpt-5.4-mini-2026-03-17`, reasoning `none`, query embedding `text-embedding-3-small` at 1,536 dimensions. The app makes one extraction call plus up to three sequential per-movie explanation calls; the earlier planning estimate of one combined explanation call is superseded for this implementation. The per-movie boundary isolates validation failures and keeps fixed catalog IDs.

## Latency and accounting

| Client measurement | Samples | Median ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: |
| first_status | 20 | 1.50 | 3.45 | 33.71 |
| first_movie | 16 | 1234.46 | 1422.98 | 1422.98 |
| first_explanation | 16 | 1896.55 | 2672.74 | 2672.74 |
| total | 20 | 5109.59 | 5751.18 | 6429.18 |

| Stage | Calls | Input tokens | Output tokens |
| --- | ---: | ---: | ---: |
| interpretation | 19 | 12221 | 1210 |
| query_embedding | 16 | 67 | 0 |
| explanation | 47 | 15399 | 5025 |

Full run: **USD 0.04877384 estimated**, with final accounting on all 20 requests. Estimate uses standard rates of USD 0.75/M chat input, 4.50/M chat output, and 0.02/M embedding input; cache discounts are ignored. This is a token-derived estimate, not a billing invoice. [Recorded rate source](../docs/research/models-and-api-budget.md). The aborted sample records only USD 0.00847740 for extraction/query embeddings; failed explanation usage and the interrupted request were not captured before the accounting fix. Its total cost and the diagnostic calls are unreported, so the full-run estimate must not be presented as total session spend.

Server timings and stage durations are retained in each terminal event. Client status timing is progress, not model first-token latency. Missing movie/text timings for no-match and clarification cases remain null. Rejected explanations correctly retain cards and discard provisional text; this fallback is correctness evidence, not proof of explanation quality.

## Proposed judgments

| Case | Proposed judgment | Reason |
| --- | --- | --- |
| 1 | Acceptable, pending human review | Friendship is well supported. Gentleness/comfort is an inference from brief overviews; human judgment is particularly important here. |
| 2 | Acceptable, pending human review | Ad Astra and Project Hail Mary support the requested premise; After Earth falls back after evidence rejection. |
| 3 | Acceptable, pending human review | Memory themes supported by Eternal Sunshine and Memento; About Time explanation falls back. |
| 4 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 5 | Acceptable, pending human review | Genre restrictions hold; La La Land explanation falls back. |
| 6 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 7 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 8 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 9 | Acceptable, pending human review | Genre/year restrictions hold; Super 8 explanation falls back. |
| 10 | Acceptable, pending human review | Only two compatible French-language Drama records are returned, correctly without padding. |
| 11 | Fail | All three explanations were rejected; cards alone do not demonstrate grounded explanation quality. |
| 12 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 13 | Fail | The Iron Giant explanation contrasts protection with conflict; the overview does not establish an absence of conflict. Treat this as an unsupported claim. |
| 14 | Fail | Unchecked actor preference leaks into semantic_query, and the (500) Days of Summer explanation may read as an unsupported negative casting claim. Warning visibility does not validate casting. |
| 15 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 16 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 17 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 18 | Fail | Reversed 2020–1990 bounds were silently reordered to 1990–2020 instead of requiring clarification. |
| 19 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |
| 20 | Acceptable, pending human review | Observed response meets the predefined outcome; details below. |

## Reviewable outputs

Judge all visible explanations in a response, not just the first card. Exact supporting quotes validate references; they do not prove every claim. Any unsupported factual claim or supported hard-constraint violation disqualifies acceptance. Inferred mood fit should remain qualified. Film facts below are the actual returned catalog records; no outside knowledge has been substituted.

### Case 1: A gentle, comforting story about friendship and community

Expected: matches; at least one comforting community/friendship story; avoid claiming guaranteed mood.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "A gentle, comforting movie about friendship and community", "included_genres": [], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**The Iron Giant** — ID 808, 1999, 86 minutes; Adventure, Animation, Drama, Family, Science Fiction.

Catalog overview: In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices.

Explanation unavailable; provisional text discarded.

**Bridge to Terabithia** — ID 955, 2007, 95 minutes; Adventure, Drama, Family.

Catalog overview: Jesse Aarons trained all summer to become the fastest runner in school. So he's very upset when newcomer Leslie Burke outruns him and everyone else. Despite this and other differences including that she's rich, he's poor, she's a city girl, and he's a country boy the two become fast friends. Together they create Terabithia, a land of monsters, trolls, ogres, and giants where they rule as king and queen.

Explanation: This may be a fit because the overview centers on two very different children who become fast friends, which matches a friendship-focused, gentle mood. The created world of Terabithia also suggests a warm shared adventure, though the community aspect is only indirect and the fit is not perfect.

Evidence: ["the two become fast friends", "Together they create Terabithia", "a land of monsters, trolls, ogres, and giants"]

**The Perks of Being a Wallflower** — ID 303, 2012, 103 minutes; Drama.

Catalog overview: Pittsburgh, Pennsylvania, 1991. High school freshman Charlie is a wallflower, always watching life from the sidelines, until two senior students, Sam and her stepbrother Patrick, become his mentors, helping him discover the joys of friendship, music and love.

Explanation: This may fit the mood because the overview centers on Charlie being helped by Sam and Patrick, with the story explicitly focusing on the joys of friendship and a growing sense of connection. The comforting angle is a bit indirect, but the emphasis on mentorship and friendship supports a gentle, community-centered feel.

Evidence: ["two senior students, Sam and her stepbrother Patrick, become his mentors", "discover the joys of friendship, music and love", "a wallflower, always watching life from the sidelines"]

Human judgment: **pending**.

### Case 2: A tense science fiction survival story in space

Expected: matches; at least one space survival story.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "A tense science fiction survival story in space", "included_genres": ["Science Fiction"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Ad Astra** — ID 623, 2019, 123 minutes; Drama, Science Fiction.

Catalog overview: The near future, a time when both hope and hardships drive humanity to look to the stars and beyond. While a mysterious phenomenon menaces to destroy life on planet Earth, astronaut Roy McBride undertakes a mission across the immensity of space and its many perils to uncover the truth about a lost expedition that decades before boldly faced emptiness and silence in search of the unknown.

Explanation: This looks like a possible fit because it centers on a mission through space with clear danger and uncertainty, which aligns with a tense survival story. The overview also emphasizes a threat to Earth and the need to uncover the truth about a lost expedition, adding to the survival-and-tension feel.

Evidence: ["a mysterious phenomenon menaces to destroy life on planet Earth", "undertakes a mission across the immensity of space and its many perils", "in search of the unknown"]

**After Earth** — ID 697, 2013, 100 minutes; Action, Adventure, Science Fiction.

Catalog overview: One thousand years after cataclysmic events forced humanity's escape from Earth, Nova Prime has become mankind's new home. Legendary General Cypher Raige returns from an extended tour of duty to his estranged family, ready to be a father to his 13-year-old son, Kitai. When an asteroid storm damages Cypher and Kitai's craft, they crash-land on a now unfamiliar and dangerous Earth. As his father lies dying in the cockpit, Kitai must trek across the hostile terrain to recover their rescue beacon. His whole life, Kitai has wanted nothing more than to be a soldier like his father. Today, he gets his chance.

Explanation unavailable; provisional text discarded.

**Project Hail Mary** — ID 494, 2026, 157 minutes; Adventure, Science Fiction.

Catalog overview: Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there. As his memory returns, he begins to uncover his mission: solve the riddle of the mysterious substance causing the sun to die out. He must call on his scientific knowledge and unorthodox ideas to save everything on Earth from extinction.

Explanation: This looks like a possible fit for a tense science fiction survival story in space because it centers on a man waking up alone on a spaceship with no memory and a mission tied to preventing extinction. The survival pressure and problem-solving focus are clear, though the mood match is based mainly on the premise rather than any explicit description of tone.

Evidence: ["wakes up on a spaceship light years from home with no recollection of who he is or how he got there", "solve the riddle of the mysterious substance causing the sun to die out", "save everything on Earth from extinction"]

Human judgment: **pending**.

### Case 3: A thoughtful story about memory and identity

Expected: matches; at least one memory/identity theme.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "A thoughtful movie about memory and identity", "included_genres": [], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Eternal Sunshine of the Spotless Mind** — ID 130, 2004, 108 minutes; Drama, Romance, Science Fiction.

Catalog overview: Joel Barish, heartbroken that his girlfriend underwent a procedure to erase him from her memory, decides to do the same. However, as he watches his memories of her fade away, he realises that he still loves her, and may be too late to correct his mistake.

Explanation: This looks like a possible fit because the story centers on a memory-erasure procedure and the lead watching memories fade, which naturally connects to memory and identity. The regret over trying to forget and realizing what still remains also suggests a reflective, thoughtful tone, though the match is only indirect from the overview.

Evidence: ["underwent a procedure to erase him from her memory", "he watches his memories of her fade away", "he still loves her"]

**Memento** — ID 129, 2000, 113 minutes; Mystery, Thriller.

Catalog overview: Leonard Shelby is tracking down the man who raped and murdered his wife. The difficulty of locating his wife's killer, however, is compounded by the fact that he suffers from a rare, untreatable form of short-term memory loss. Although he can recall details of life before his accident, Leonard cannot remember what happened fifteen minutes ago, where he's going, or why.

Explanation: This may fit a thoughtful mood about memory and identity because the overview centers on Leonard’s short-term memory loss and how it affects what he can remember about himself and his pursuit. The mystery around his wife’s killer is tied directly to his inability to hold on to recent events, which makes the memory theme especially central, though the fit is more thematic than reflective.

Evidence: ["suffers from a rare, untreatable form of short-term memory loss", "he can recall details of life before his accident", "Leonard cannot remember what happened fifteen minutes ago"]

**About Time** — ID 416, 2013, 123 minutes; Drama, Fantasy, Romance.

Catalog overview: The night after another unsatisfactory New Year's party, Tim's father reveals to him that the men in their family have the ability to travel through time. They can't change history, but they can change what happens and has happened in their own lives. Thus begins the start of a lesson in learning to appreciate life itself as it is, as it comes, and most importantly, the people living alongside us.

Explanation unavailable; provisional text discarded.

Human judgment: **pending**.

### Case 4: An adventurous animated film with a hopeful feeling

Expected: matches; all Animation; at least one hopeful adventure.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie with adventurous and hopeful feeling", "included_genres": ["Animation", "Adventure"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Up** — ID 53, 2009, 96 minutes; Adventure, Animation, Comedy, Family.

Catalog overview: Carl Fredricksen spent his entire life dreaming of exploring the globe and experiencing life to its fullest. But at age 78, life seems to have passed him by, until a twist of fate (and a persistent 8-year old Wilderness Explorer named Russell) gives him a new lease on life.

Explanation: This could fit an adventurous and hopeful mood because the overview centers on a lifelong dream of exploring the globe and then a “new lease on life” after an unexpected twist of fate. That suggests both adventure and a positive turn, though the fit is based only on the brief synopsis.

Evidence: ["dreaming of exploring the globe", "a twist of fate", "gives him a new lease on life"]

**Onward** — ID 744, 2020, 102 minutes; Adventure, Animation, Comedy, Family, Fantasy.

Catalog overview: In a suburban fantasy world, two teenage elf brothers embark on an extraordinary quest to discover if there is still a little magic left out there.

Explanation: This seems like a possible fit for an adventurous, hopeful feeling because it centers on brothers who "embark on an extraordinary quest" in a fantasy world, which suggests active exploration and discovery. The idea of trying to find out whether "there is still a little magic left out there" also gives it a hopeful tone.

Evidence: ["embark on an extraordinary quest", "to discover if there is still a little magic left out there", "In a suburban fantasy world"]

**Anastasia** — ID 918, 1997, 94 minutes; Adventure, Animation, Family, Fantasy.

Catalog overview: Ten years after she was separated from her family, an eighteen-year-old orphan with vague memories of the past sets out to Paris in hopes of reuniting with her grandmother. She is accompanied by two con men, who intend to pass her off as the Grand Duchess Anastasia to the Dowager Empress for a reward.

Explanation: This may fit an adventurous, hopeful mood because the story follows an orphan setting out to Paris in hopes of reuniting with her grandmother, with the journey and impersonation plot adding a sense of forward motion and adventure. The fit is plausible, though the overview emphasizes a reunion quest more than the mood itself.

Evidence: ["sets out to Paris in hopes of reuniting with her grandmother", "She is accompanied by two con men", "to pass her off as the Grand Duchess Anastasia"]

Human judgment: **pending**.

### Case 5: A romantic comedy, no horror

Expected: matches; all Romance AND Comedy; no Horror.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie with romantic and comedic themes", "included_genres": ["Comedy", "Romance"], "excluded_genres": ["Horror"], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Just Go with It** — ID 832, 2011, 117 minutes; Comedy, Romance.

Catalog overview: While romancing Palmer, a much younger schoolteacher, plastic surgeon Danny Maccabee enlists his loyal assistant Katherine to pretend to be his soon to be ex-wife, in order to cover up a careless lie. When more lies backfire, Katherine's kids become involved, and everyone heads off for a weekend in Hawaii that will change all their lives.

Explanation: This looks like a possible fit for romantic and comedic themes because the overview centers on romancing Palmer and on a chain of lies that creates comic complications. The setup also includes a weekend in Hawaii where the situation escalates, which supports the romance-comedy angle, though the fit is fairly straightforward rather than especially distinctive.

Evidence: ["romancing Palmer", "in order to cover up a careless lie", "everyone heads off for a weekend in Hawaii that will change all their lives"]

**La La Land** — ID 100, 2016, 129 minutes; Comedy, Drama, Romance.

Catalog overview: Mia, an aspiring actress, serves lattes to movie stars in between auditions and Sebastian, a jazz musician, scrapes by playing cocktail party gigs in dingy bars, but as success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair, and the dreams they worked so hard to maintain in each other threaten to rip them apart.

Explanation unavailable; provisional text discarded.

**Lost in Translation** — ID 525, 2003, 102 minutes; Comedy, Drama, Romance.

Catalog overview: Two lost souls visiting Tokyo -- the young, neglected wife of a photographer and a washed-up movie star shooting a TV commercial -- find an odd solace and pensive freedom to be real in each other's company, away from their lives in America.

Explanation: This seems like a possible fit for romantic and comedic themes because the overview explicitly describes an odd solace found in each other's company between two people, while the situation itself includes an unusual, lightly comic setup in Tokyo. The romance angle is present, though the mood is more pensive than broadly cheerful, so the fit is somewhat partial.

Evidence: ["odd solace", "in each other's company", "Two lost souls visiting Tokyo"]

Human judgment: **pending**.

### Case 6: A crime thriller with no comedy

Expected: matches; all Crime AND Thriller; no Comedy.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "crime thriller movie", "included_genres": ["Crime", "Thriller"], "excluded_genres": ["Comedy"], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Inside Man** — ID 768, 2006, 129 minutes; Crime, Drama, Thriller.

Catalog overview: When an armed, masked gang enter a Manhattan bank, lock the doors and take hostages, the detective assigned to effect their release enters negotiations preoccupied with corruption charges he is facing.

Explanation: This looks like a possible fit for a crime thriller because it centers on an armed bank takeover, hostages, and a detective negotiating under pressure while facing corruption charges. The setup suggests criminal tension and procedural conflict, though the mood match is based only on the plot description.

Evidence: ["armed, masked gang enter a Manhattan bank", "lock the doors and take hostages", "the detective assigned to effect their release enters negotiations preoccupied with corruption charges"]

**Law Abiding Citizen** — ID 891, 2009, 109 minutes; Crime, Drama, Thriller.

Catalog overview: A frustrated man decides to take justice into his own hands after a plea bargain sets one of his family's killers free. He targets not only the killer but also the district attorney and others involved in the deal.

Explanation: This looks like a possible fit for a crime thriller because the overview centers on justice, a plea bargain, and a man targeting people involved in the deal, which suggests a crime-driven conflict with thriller tension. The crime and drama genres also align with that mood, though the fit is fairly direct rather than especially distinctive.

Evidence: ["take justice into his own hands", "a plea bargain sets one of his family's killers free", "He targets not only the killer but also the district attorney and others involved in the deal"]

**Prisoners** — ID 216, 2013, 153 minutes; Crime, Drama, Thriller.

Catalog overview: After his six-year-old daughter is abducted, a desperate father takes justice into his own hands when he loses faith in the detective leading the investigation, setting both men on a collision course as the search descends into obsession and moral compromise.

Explanation: This looks like a possible fit for a crime thriller because the story centers on an abduction investigation, a desperate father's vigilante turn, and a tense conflict that escalates into obsession and moral compromise.

Evidence: ["abducted", "takes justice into his own hands", "the search descends into obsession and moral compromise"]

Human judgment: **pending**.

### Case 7: A drama under 90 minutes

Expected: matches; all Drama; runtime strictly <90.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Drama"], "excluded_genres": [], "runtime_minutes": 90, "runtime_operator": "lt", "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**The Iron Giant** — ID 808, 1999, 86 minutes; Adventure, Animation, Drama, Family, Science Fiction.

Catalog overview: In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices.

Explanation: This could fit a movie mood focused on friendship, growing empathy, and overcoming fear: a giant machine befriends a boy and then acts selflessly to protect others. The setting also suggests a small-town, emotionally grounded story with themes of prejudice and humanity.

Evidence: ["a giant metal machine befriends a nine-year-old boy", "finds its humanity", "saving people from their own fears and prejudices"]

**Stand by Me** — ID 732, 1986, 89 minutes; Adventure, Drama.

Catalog overview: After learning that a boy their age has been accidentally killed near their rural homes, four boys decide to go see the body. Gordie, Vern, Chris, and Teddy encounter a mean junk man and a marsh full of leeches, but they also learn more about one another and their very different home lives. Just a lark at first, the boys' adventure evolves into a defining event in their lives.

Explanation: This could fit if the mood/theme is simply a movie about a memorable coming-of-age journey, since the boys’ trip starts as a dare and becomes important to their lives. The rural setting and focus on friendship and different home lives also support that kind of reflective adventure.

Evidence: ["four boys decide to go see the body", "they also learn more about one another and their very different home lives", "the boys' adventure evolves into a defining event in their lives"]

**Grave of the Fireflies** — ID 710, 1988, 89 minutes; Animation, Drama, War.

Catalog overview: In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan. After a falling out with their aunt, they move into an abandoned bomb shelter. With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive.

Explanation: This could fit if the mood/theme is simply “movie,” because the overview centers on a wartime survival story with clear dramatic stakes: orphaned siblings, an abandoned bomb shelter, and a struggle to survive after their rations run out. If a more specific theme was intended, the connection is too broad to judge precisely.

Evidence: ["In the final months of World War II", "orphaned when their mother is killed during an air raid in Kobe, Japan", "Seita and Setsuko struggle to survive"]

Human judgment: **pending**.

### Case 8: An animated film at most 90 minutes

Expected: matches; all Animation; runtime <=90.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Animation"], "excluded_genres": [], "runtime_minutes": 90, "runtime_operator": "lte", "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**The Simpsons Movie** — ID 490, 2007, 87 minutes; Animation, Comedy, Family.

Catalog overview: After Homer accidentally pollutes the town's water supply, Springfield is encased in a gigantic dome by the EPA and the Simpsons are declared fugitives.

Explanation: This could fit a light, chaotic movie mood because the plot centers on a family-scale mishap that escalates into a townwide crisis. The combination of accidental pollution, a giant dome, and the Simpsons becoming fugitives suggests fast, comedic disorder rather than a serious drama.

Evidence: ["After Homer accidentally pollutes the town's water supply", "Springfield is encased in a gigantic dome by the EPA", "the Simpsons are declared fugitives"]

**Shark Tale** — ID 720, 2004, 90 minutes; Action, Animation, Comedy, Family.

Catalog overview: Oscar is a small fish whose big aspirations often get him into trouble. Meanwhile, Lenny is a great white shark with a surprising secret that no sea creature would guess: He's a vegetarian. When a lie turns Oscar into an improbable hero and Lenny becomes an outcast, the two form an unlikely friendship.

Explanation: This could fit a general movie mood because the overview centers on a light, story-driven setup with comic conflict and an unlikely friendship. The big aspirations, lie, and surprising secret suggest a playful adventure tone, though the match to the broad theme is fairly loose.

Evidence: ["Oscar is a small fish whose big aspirations often get him into trouble.", "a lie turns Oscar into an improbable hero", "the two form an unlikely friendship"]

**Mulan** — ID 354, 1998, 88 minutes; Adventure, Animation, Family.

Catalog overview: When Imperial China calls one man from every family to defend the empire from invading Huns, a young woman disguises herself as a soldier to take her ailing father’s place. Facing ruthless invaders, brutal training, and the risk of execution if discovered, she must decide who she truly is—and what she’s willing to fight for.

Explanation: This could fit a movie mood/theme if you want an adventure centered on disguise, duty, and self-discovery. The overview points to a protagonist facing conflict and training while deciding who she truly is, which may suit a story-driven, action-oriented pick.

Evidence: ["a young woman disguises herself as a soldier", "Facing ruthless invaders, brutal training", "she must decide who she truly is"]

Human judgment: **pending**.

### Case 9: A science fiction film released from 2010 through 2020

Expected: matches; all Science Fiction; 2010<=year<=2020.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Science Fiction"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": 2010, "year_max": 2020, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Super 8** — ID 646, 2011, 112 minutes; Mystery, Science Fiction, Thriller.

Catalog overview: In late 1970s Ohio, a group of friends filming a homemade zombie movie witness a devastating train derailment. Soon after, their quiet town is gripped by unexplained disappearances, strange phenomena, and a growing sense of fear, as they uncover that something terrifying has been set loose.

Explanation unavailable; provisional text discarded.

**Looper** — ID 320, 2012, 118 minutes; Action, Science Fiction, Thriller.

Catalog overview: In the year 2044, time travel has not yet been invented but in 30 years it will have been. When the mob wants to get rid of someone, they will send their target into the past where a looper, a hired gun, like Joe is waiting to mop up. Joe is getting rich and life is good until the day the mob decides to close the loop, sending back Joe's future self for assassination.

Explanation: This may fit a movie mood because the overview centers on a fast, high-stakes science-fiction crime setup with a hired gun, time travel, and an assassination plot. The escalating conflict around "closing the loop" suggests an action-thriller structure, though the mood match is fairly broad.

Evidence: ["time travel has not yet been invented but in 30 years it will have been", "When the mob wants to get rid of someone", "sending back Joe's future self for assassination"]

**Godzilla** — ID 387, 2014, 123 minutes; Action, Drama, Science Fiction.

Catalog overview: Ford Brody, a Navy bomb expert, has just reunited with his family in San Francisco when he is forced to go to Japan to help his estranged father, Joe. Soon, both men are swept up in an escalating crisis when an ancient alpha predator arises from the sea to combat malevolent adversaries that threaten the survival of humanity. The creatures leave colossal destruction in their wake, as they make their way toward their final battleground: San Francisco.

Explanation: This could fit if you want a large-scale action-driven movie centered on a crisis threatening humanity, with family tension woven into the plot. The overview also suggests a dramatic, destructive buildup toward a final battleground, though the mood/theme match is fairly broad.

Evidence: ["an ancient alpha predator arises from the sea", "malevolent adversaries that threaten the survival of humanity", "The creatures leave colossal destruction in their wake"]

Human judgment: **pending**.

### Case 10: A drama originally in French

Expected: matches; all Drama; original_language fr.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Drama"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": "fr", "unsupported_requirements": [], "clarification": []}`

**Léon: The Professional** — ID 137, 1994, 111 minutes; Action, Crime, Drama.

Catalog overview: Léon, the top hit man in New York, has earned a rep as an effective "cleaner". But when his next-door neighbors are wiped out by a loose-cannon DEA agent, he becomes the unwilling custodian of 12-year-old Mathilda. Before long, Mathilda's thoughts turn to revenge, and she considers following in Léon's footsteps.

Explanation: This could fit a crime/action movie mood because it centers on a hit man in New York, a violent killing of neighbors, and a revenge-driven plot that follows. The dramatic guardian relationship adds a tense edge, though the mood/themes are fairly broad here.

Evidence: ["the top hit man in New York", "when his next-door neighbors are wiped out by a loose-cannon DEA agent", "Mathilda's thoughts turn to revenge"]

**The Intouchables** — ID 93, 2011, 113 minutes; Comedy, Drama.

Catalog overview: A true story of two men who should never have met – a quadriplegic aristocrat who was injured in a paragliding accident and a young man from the projects.

Explanation: This could fit a movie mood because it centers on an unexpected connection between two very different people, framed through both comedy and drama. The overview’s contrast between an aristocrat and a young man from the projects suggests a relationship-driven story with social differences at its core, though the mood match is fairly general.

Evidence: ["A true story of two men who should never have met", "a quadriplegic aristocrat who was injured in a paragliding accident", "a young man from the projects"]

Human judgment: **pending**.

### Case 11: A Japanese animated film

Expected: matches; all Animation; original_language ja.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "Japanese animated movie", "included_genres": ["Animation"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": "ja", "unsupported_requirements": [], "clarification": []}`

**Spirited Away** — ID 90, 2001, 125 minutes; Animation, Family, Fantasy.

Catalog overview: A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must call upon the courage she never knew she had to free her family.

Explanation unavailable; provisional text discarded.

**Grave of the Fireflies** — ID 710, 1988, 89 minutes; Animation, Drama, War.

Catalog overview: In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan. After a falling out with their aunt, they move into an abandoned bomb shelter. With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive.

Explanation unavailable; provisional text discarded.

**Princess Mononoke** — ID 436, 1997, 134 minutes; Adventure, Animation, Fantasy.

Catalog overview: Ashitaka, a prince of the disappearing Emishi people, is cursed by a demonized boar god and must journey to the west to find a cure. Along the way, he encounters San, a young human woman fighting to protect the forest, and Lady Eboshi, who is trying to destroy it. Ashitaka must find a way to bring balance to this conflict.

Explanation unavailable; provisional text discarded.

Human judgment: **pending**.

### Case 12: A comedy released before 2000, no romance

Expected: matches; all Comedy; year<=1999; no Romance.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Comedy"], "excluded_genres": ["Romance"], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": 1999, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Ferris Bueller's Day Off** — ID 932, 1986, 103 minutes; Comedy.

Catalog overview: After high school slacker Ferris Bueller successfully fakes an illness in order to skip school for the day, he goes on a series of adventures throughout Chicago with his girlfriend Sloane and best friend Cameron, all the while trying to outwit his wily school principal and fed-up sister.

Explanation: This looks like a possible fit if the mood is simply for a light comedy with playful mischief and a day-long escapade. The overview centers on skipping school, adventures around Chicago, and outwitting authority figures, which matches a breezy, humorous movie vibe.

Evidence: ["fakes an illness in order to skip school for the day", "goes on a series of adventures throughout Chicago", "trying to outwit his wily school principal and fed-up sister"]

**The Big Lebowski** — ID 252, 1998, 117 minutes; Comedy, Crime.

Catalog overview: Jeffrey 'The Dude' Lebowski, a Los Angeles slacker who only wants to bowl and drink White Russians, is mistaken for another Jeffrey Lebowski, a wheelchair-bound millionaire, and finds himself dragged into a strange series of events involving nihilists, adult film producers, ferrets, errant toes, and large sums of money.

Explanation: This could fit a movie mood in a broad, easygoing sense because it centers on a slacker's life getting pulled into an odd chain of events, mixing comedy with crime. The offbeat mix of bowling, mistaken identity, and bizarre trouble suggests a playful, quirky watch rather than something straightforward.

Evidence: ["a Los Angeles slacker who only wants to bowl and drink White Russians", "is mistaken for another Jeffrey Lebowski", "finds himself dragged into a strange series of events"]

**The Truman Show** — ID 66, 1998, 103 minutes; Comedy, Drama.

Catalog overview: In a picture-perfect seaside town, an insurance salesman begins to realize that his entire existence may be staged and observed by a vast unseen audience as part of a long-running real-time reality TV show.

Explanation: This could fit a reflective or reality-questioning mood because the overview centers on a man who starts to suspect his life is artificially constructed and watched. The idea of a "picture-perfect" setting hiding a staged existence suggests themes of surveillance, control, and uncertainty, though the connection to the supplied theme is quite broad.

Evidence: ["picture-perfect seaside town", "his entire existence may be staged and observed", "a vast unseen audience"]

Human judgment: **pending**.

### Case 13: A comforting movie on Netflix

Expected: matches with visible Netflix unchecked warning; no availability claim.

Observed: `matches`. Movies match your supported restrictions. Some requirements were not checked; see the warnings below.

Interpretation: `{"semantic_query": "comforting movie", "included_genres": [], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": ["Netflix availability"], "clarification": []}`

**The Green Mile** — ID 80, 1999, 189 minutes; Crime, Drama, Fantasy.

Catalog overview: A supernatural tale set on death row in a Southern prison, where gentle giant John Coffey possesses the mysterious power to heal people's ailments. When the cell block's head guard, Paul Edgecomb, recognizes Coffey's miraculous gift, he tries desperately to help stave off the condemned man's execution.

Explanation: This could be a possible fit for a comforting movie because the overview centers on a gentle character with a healing gift and a guard who tries to help him, which may create a caring, hopeful thread. That said, the death row setting makes the connection only a partial fit.

Evidence: ["gentle giant John Coffey possesses the mysterious power to heal people's ailments", "he tries desperately to help stave off the condemned man's execution", "A supernatural tale set on death row in a Southern prison"]

**The Iron Giant** — ID 808, 1999, 86 minutes; Adventure, Animation, Drama, Family, Science Fiction.

Catalog overview: In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices.

Explanation: This could be a fit for a comforting movie because it centers on a gentle friendship between a boy and a giant machine, and the story moves toward kindness and protection rather than conflict. The small-town setting and the idea of finding humanity through unselfish saving also support a warm, reassuring tone.

Evidence: ["befriends a nine-year-old boy", "finds its humanity", "unselfishly saving people from their own fears and prejudices"]

**Hachi: A Dog's Tale** — ID 641, 2009, 93 minutes; Drama, Family.

Catalog overview: Professor Wilson discovers a lost Akita puppy on his way home. Despite objections from his wife, Hachi endears himself to the family and grows to be Parker's loyal companion. As their bond grows deeper, a beautiful relationship unfolds.

Explanation: This could fit a comforting movie mood because it centers on a gentle homecoming and the gradual warmth of a loyal companion becoming part of the family. The overview suggests a tender, reassuring relationship rather than conflict-driven action, though the fit is somewhat general.

Evidence: ["Hachi endears himself to the family", "grows to be Parker's loyal companion", "a beautiful relationship unfolds"]

Human judgment: **pending**.

### Case 14: A drama starring Tom Hanks

Expected: matches with visible actor unchecked warning; no casting claim.

Observed: `matches`. Movies match your supported restrictions. Some requirements were not checked; see the warnings below.

Interpretation: `{"semantic_query": "movie with drama mood/themes, starring Tom Hanks", "included_genres": ["Drama"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": ["starring Tom Hanks"], "clarification": []}`

**Captain Phillips** — ID 594, 2013, 134 minutes; Action, Drama, Thriller.

Catalog overview: The true story of Captain Richard Phillips and the 2009 hijacking by Somali pirates of the US-flagged MV Maersk Alabama, the first American cargo ship to be hijacked in two hundred years.

Explanation: This could fit a drama mood because the overview centers on a true-story hijacking, which suggests a tense, serious conflict-driven setup. The connection to "starring Tom Hanks" is weak here because that detail is not present in the supplied overview.

Evidence: ["The true story of Captain Richard Phillips", "the 2009 hijacking by Somali pirates", "The true story"]

**(500) Days of Summer** — ID 312, 2009, 95 minutes; Comedy, Drama, Romance.

Catalog overview: Tom, greeting-card writer and hopeless romantic, is caught completely off-guard when his girlfriend, Summer, suddenly dumps him. He reflects on their 500 days together to try to figure out where their love affair went sour, and in doing so, Tom rediscovers his true passions in life.

Explanation: This could fit the drama mood/theme because it centers on a breakup and Tom’s reflection on how the relationship “went sour,” which gives it a more serious emotional angle. The “starring Tom Hanks” part does not match the provided movie data, so that part is a weak fit here.

Evidence: ["Tom, greeting-card writer and hopeless romantic, is caught completely off-guard when his girlfriend, Summer, suddenly dumps him.", "He reflects on their 500 days together to try to figure out where their love affair went sour,", "and in doing so, Tom rediscovers his true passions in life."]

**Hachi: A Dog's Tale** — ID 641, 2009, 93 minutes; Drama, Family.

Catalog overview: Professor Wilson discovers a lost Akita puppy on his way home. Despite objections from his wife, Hachi endears himself to the family and grows to be Parker's loyal companion. As their bond grows deeper, a beautiful relationship unfolds.

Explanation: This looks like a possible fit for a drama mood because the overview centers on a deep, emotional bond and a relationship that unfolds over time. The connection to “starring Tom Hanks” is not supported by the supplied catalog facts, so that part of the prompt cannot be confirmed here.

Evidence: ["a beautiful relationship unfolds", "their bond grows deeper", "loyal companion"]

Human judgment: **pending**.

### Case 15: A film under 1 minute

Expected: no_match; catalog-backed runtime alternative; no automatic selection.

Observed: `no_match`. No movies meet these restrictions. Select an optional change; counts show filter eligibility, not relevance.

Interpretation: `{"semantic_query": "movie", "included_genres": [], "excluded_genres": [], "runtime_minutes": 1, "runtime_operator": "lt", "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

Offered changes: Change runtime from under 1 minute to under 65 minutes (+64 minutes) (1 eligible)

Human judgment: **pending**.

### Case 16: A movie released from 1800 through 1801 under 1 minute

Expected: no_match; no single-change alternative; invite edit.

Observed: `no_match`. No single-constraint change produces catalog matches. Please edit your request.

Interpretation: `{"semantic_query": "movie", "included_genres": [], "excluded_genres": [], "runtime_minutes": 1, "runtime_operator": "lt", "year_min": 1800, "year_max": 1801, "original_language": null, "unsupported_requirements": [], "clarification": []}`

Human judgment: **pending**.

### Case 17: A comedy but exclude comedy

Expected: clarification; no cards.

Observed: `clarification`. Please clarify or edit your request; interpretation was incomplete or invalid.

Human judgment: **pending**.

### Case 18: A drama released from 2020 through 1990

Expected: clarification; no cards.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "movie", "included_genres": ["Drama"], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": 1990, "year_max": 2020, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**La La Land** — ID 100, 2016, 129 minutes; Comedy, Drama, Romance.

Catalog overview: Mia, an aspiring actress, serves lattes to movie stars in between auditions and Sebastian, a jazz musician, scrapes by playing cocktail party gigs in dingy bars, but as success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair, and the dreams they worked so hard to maintain in each other threaten to rip them apart.

Explanation: This could fit a movie mood centered on pursuing creative dreams and the strain that success can place on a relationship. The overview highlights two artists chasing their ambitions while their love affair is tested by difficult choices, which makes the fit plausible.

Evidence: ["aspiring actress", "a jazz musician", "success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair"]

**Once Upon a Time in… Hollywood** — ID 161, 2019, 162 minutes; Comedy, Drama, Thriller.

Catalog overview: Los Angeles, 1969. TV star Rick Dalton, a struggling actor specializing in westerns, and stuntman Cliff Booth, his best friend, try to survive in a constantly changing movie industry. Dalton is the neighbor of the young and promising actress and model Sharon Tate, who has just married the prestigious Polish director Roman Polanski…

Explanation: This could fit a movie-themed mood because it centers on people working inside Hollywood and the changing movie industry, with a TV star, a struggling actor, and a stuntman trying to get by. The connection is fairly direct, though the overview gives more industry setting than a broad celebration of movies.

Evidence: ["TV star Rick Dalton, a struggling actor specializing in westerns, and stuntman Cliff Booth", "try to survive in a constantly changing movie industry", "Los Angeles, 1969"]

**Ford v Ferrari** — ID 435, 2019, 153 minutes; Action, Drama, History.

Catalog overview: American car designer Carroll Shelby and the British-born driver Ken Miles work together to battle corporate interference, the laws of physics, and their own personal demons to build a revolutionary race car for Ford Motor Company and take on the dominating race cars of Enzo Ferrari at the 24 Hours of Le Mans in France in 1966.

Explanation: This could fit a general movie mood/theme in a broad sense because it centers on a high-stakes, dramatic competition with teamwork, conflict, and historical racing. The overview suggests an action-driven story with personal and external obstacles, though the mood/themes provided are very generic, so the connection is fairly weak.

Evidence: ["work together to battle corporate interference", "the laws of physics, and their own personal demons", "take on the dominating race cars of Enzo Ferrari"]

Human judgment: **pending**.

### Case 19: A movie in English or French; I have not decided which original language

Expected: clarification; no guessed language; no cards.

Observed: `clarification`. Please clarify or edit your request before searching.

Interpretation: `{"semantic_query": "movie", "included_genres": [], "excluded_genres": [], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": ["Do you want the original language to be English or French?"]}`

Human judgment: **pending**.

### Case 20: A quiet reflective drama about grief, no horror

Expected: matches; all Drama; no Horror; at least one reflective grief story.

Observed: `matches`. Semantic matches from the local movie catalog. Supported constraints were checked.

Interpretation: `{"semantic_query": "A quiet reflective movie about grief", "included_genres": ["Drama"], "excluded_genres": ["Horror"], "runtime_minutes": null, "runtime_operator": null, "year_min": null, "year_max": null, "original_language": null, "unsupported_requirements": [], "clarification": []}`

**Collateral Beauty** — ID 938, 2016, 97 minutes; Drama, Romance.

Catalog overview: Retreating from life after a tragedy, a man questions the universe by writing to Love, Time and Death. Receiving unexpected answers, he begins to see how these things interlock and how even loss can reveal moments of meaning and beauty.

Explanation: This looks like a possible fit for a quiet reflective movie about grief because the overview centers on retreating after a tragedy and questioning life through letters to abstract ideas. It also directly frames loss as something that can reveal meaning and beauty, which aligns with reflective grief themes.

Evidence: ["Retreating from life after a tragedy", "he begins to see how these things interlock", "even loss can reveal moments of meaning and beauty"]

**Eternal Sunshine of the Spotless Mind** — ID 130, 2004, 108 minutes; Drama, Romance, Science Fiction.

Catalog overview: Joel Barish, heartbroken that his girlfriend underwent a procedure to erase him from her memory, decides to do the same. However, as he watches his memories of her fade away, he realises that he still loves her, and may be too late to correct his mistake.

Explanation: This could fit a quiet reflective mood because the story centers on a man privately confronting heartbreak and looking back through fading memories. The grief angle is suggested by his realization that he still loves her as the memories disappear, though the sci-fi premise makes the fit only partial.

Evidence: ["heartbroken that his girlfriend underwent a procedure to erase him from her memory", "as he watches his memories of her fade away", "he realises that he still loves her"]

**Grave of the Fireflies** — ID 710, 1988, 89 minutes; Animation, Drama, War.

Catalog overview: In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan. After a falling out with their aunt, they move into an abandoned bomb shelter. With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive.

Explanation: This could fit a quiet reflective mood about grief because the overview centers on two children becoming orphaned, then trying to survive after a family loss. The focus on their struggle and isolation suggests a somber, contemplative story, though the war setting makes the fit only partial.

Evidence: ["orphaned when their mother is killed during an air raid in Kobe, Japan", "move into an abandoned bomb shelter", "Seita and Setsuko struggle to survive"]

Human judgment: **pending**.
