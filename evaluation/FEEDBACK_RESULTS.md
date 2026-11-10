# T4 follow-up verification — 2026-11-10

The owner feedback and accepted scope are recorded in [HUMAN_REVIEW.md](HUMAN_REVIEW.md). This is a supplementary nine-case verification run, not a replacement for the original 20-case human review or a newly inferred human score.

The unchanged prompts/expectations in `feedback-requests-2026-11-10.json` were fixed before follow-up calls. The first run used case-insensitive quote recovery and still produced two fallbacks; `feedback-live-2026-11-10.jsonl` is retained. After diagnosis identified evidence-list/schema violations too, the final run uses native strict JSON Schema and server-resolved reference IDs. `feedback-live-references-2026-11-10.jsonl` retains every final event.

**Final bounded sample: 27/27 explanations completed across nine requests, with zero explanation fallbacks.** Every returned ID belongs to the server-selected records, every evidence excerpt occurs verbatim in that record, and independently checked supported genre/runtime/year/language restrictions hold. Language assertions use read-only catalog original-language fields. Case 19 allows English OR French, without requiring one result in each language.

**Grounding failure found in follow-up case 14:** the `(500) Days of Summer`
explanation says Tom spends the next 500 days looking back after being dumped.
The overview's 500 days describe the relationship, not a post-breakup reflection
period. That explanation is unsupported, so **case 14 is not a grounded pass**.
The raw output is preserved below. The 27/27 figure establishes completion, not
semantic correctness. The final prompt now explicitly preserves chronology,
quantities, durations and causal relationships; that guidance is not a proven
semantic filter, and no replacement run is used to erase this failure.

The natural explanation prompt leads with concrete story details, removes generic fit verdicts, and retains specific uncertainty for unchecked facts such as cast. Structural references and the sample do not prove universal grounding or provider reliability. The original reversed-year expectation mismatch is recorded, not silently repaired or waived.

Final recorded token-derived cost estimate: **USD 0.02996709**, with final accounting on all 9 requests. The earlier nine-case sample records USD 0.02978034. These exclude diagnostic/reproduction calls and are not total-session charges or settled invoices. No retries, catalog reload, embedding reindex, schema migration, external tracing, or AWS operations were involved.

| Case | Catalog cards | Completed explanations | Original languages | Grounding review |
| --- | ---: | ---: | --- | --- |
| 1 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 2 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 3 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 5 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 7 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 9 | 3 | 3 | unrestricted | No specific failure identified; no new human score |
| 11 | 3 | 3 | ja | No specific failure identified; no new human score |
| 14 | 3 | 3 | unrestricted | Failed: changed 500-day timeline |
| 19 | 3 | 3 | en, fr | No specific failure identified; no new human score |

## Actual final outputs

### Case 1: A gentle, comforting story about friendship and community

Expected: matches; at least one comforting community/friendship story; avoid claiming guaranteed mood; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**The Iron Giant** — 1999, 86 minutes, original language `en`; Adventure, Animation, Drama, Family, Science Fiction.

A giant metal machine befriends a nine-year-old boy in small-town Maine, and their bond grows as the machine ultimately saves people from their own fears and prejudices. That story centers friendship and community in a gentle way through the boy and the town’s response to the giant.

Catalog overview: In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices.

Server-resolved evidence: ["In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices."]

**Bridge to Terabithia** — 2007, 95 minutes, original language `en`; Adventure, Drama, Family.

Jesse Aarons is upset when newcomer Leslie Burke outruns him, but the two soon become fast friends despite their differences in wealth and background. Together they create Terabithia, a shared world where they rule as king and queen, centering the story on friendship and imagination.

Catalog overview: Jesse Aarons trained all summer to become the fastest runner in school. So he's very upset when newcomer Leslie Burke outruns him and everyone else. Despite this and other differences including that she's rich, he's poor, she's a city girl, and he's a country boy the two become fast friends. Together they create Terabithia, a land of monsters, trolls, ogres, and giants where they rule as king and queen.

Server-resolved evidence: ["So he's very upset when newcomer Leslie Burke outruns him and everyone else.", "Despite this and other differences including that she's rich, he's poor, she's a city girl, and he's a country boy the two become fast friends.", "Together they create Terabithia, a land of monsters, trolls, ogres, and giants where they rule as king and queen."]

**The Perks of Being a Wallflower** — 2012, 103 minutes, original language `en`; Drama.

Set in 1991 Pittsburgh, the story follows shy freshman Charlie as two older students, Sam and Patrick, take him under their wing and help him discover friendship, music, and love. That makes the film centered on community and connection through a supportive friendship circle.

Catalog overview: Pittsburgh, Pennsylvania, 1991. High school freshman Charlie is a wallflower, always watching life from the sidelines, until two senior students, Sam and her stepbrother Patrick, become his mentors, helping him discover the joys of friendship, music and love.

Server-resolved evidence: ["Pittsburgh, Pennsylvania, 1991.", "High school freshman Charlie is a wallflower, always watching life from the sidelines, until two senior students, Sam and her stepbrother Patrick, become his mentors, helping him discover the joys of friendship, music and love."]

### Case 2: A tense science fiction survival story in space

Expected: matches; at least one space survival story; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Ad Astra** — 2019, 123 minutes, original language `en`; Drama, Science Fiction.

A mysterious phenomenon threatens life on Earth, and astronaut Roy McBride crosses deep space and its many perils to uncover the truth behind a lost expedition. The story centers on tense survival and a search through emptiness and silence in the near future.

Catalog overview: The near future, a time when both hope and hardships drive humanity to look to the stars and beyond. While a mysterious phenomenon menaces to destroy life on planet Earth, astronaut Roy McBride undertakes a mission across the immensity of space and its many perils to uncover the truth about a lost expedition that decades before boldly faced emptiness and silence in search of the unknown.

Server-resolved evidence: ["While a mysterious phenomenon menaces to destroy life on planet Earth, astronaut Roy McBride undertakes a mission across the immensity of space and its many perils to uncover the truth about a lost expedition that decades before boldly faced emptiness and silence in search of the unknown.", "The near future, a time when both hope and hardships drive humanity to look to the stars and beyond."]

**After Earth** — 2013, 100 minutes, original language `en`; Action, Adventure, Science Fiction.

After an asteroid storm leaves Cypher wounded and Kitai stranded on a dangerous, unfamiliar Earth, the story turns into a survival trek as Kitai crosses hostile terrain to recover their rescue beacon. The added father-son tension comes from Cypher returning to his estranged family and Kitai trying to live up to his soldier father.

Catalog overview: One thousand years after cataclysmic events forced humanity's escape from Earth, Nova Prime has become mankind's new home. Legendary General Cypher Raige returns from an extended tour of duty to his estranged family, ready to be a father to his 13-year-old son, Kitai. When an asteroid storm damages Cypher and Kitai's craft, they crash-land on a now unfamiliar and dangerous Earth. As his father lies dying in the cockpit, Kitai must trek across the hostile terrain to recover their rescue beacon. His whole life, Kitai has wanted nothing more than to be a soldier like his father. Today, he gets his chance.

Server-resolved evidence: ["When an asteroid storm damages Cypher and Kitai's craft, they crash-land on a now unfamiliar and dangerous Earth.", "As his father lies dying in the cockpit, Kitai must trek across the hostile terrain to recover their rescue beacon.", "Legendary General Cypher Raige returns from an extended tour of duty to his estranged family, ready to be a father to his 13-year-old son, Kitai."]

**Project Hail Mary** — 2026, 157 minutes, original language `en`; Adventure, Science Fiction.

Ryland Grace wakes up alone on a spaceship with no memory of how he got there, then has to use science and unorthodox ideas to solve why the sun is dying out and save Earth from extinction. That puts the story squarely in tense space-based survival and problem-solving territory.

Catalog overview: Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there. As his memory returns, he begins to uncover his mission: solve the riddle of the mysterious substance causing the sun to die out. He must call on his scientific knowledge and unorthodox ideas to save everything on Earth from extinction.

Server-resolved evidence: ["Science teacher Ryland Grace wakes up on a spaceship light years from home with no recollection of who he is or how he got there.", "As his memory returns, he begins to uncover his mission: solve the riddle of the mysterious substance causing the sun to die out.", "He must call on his scientific knowledge and unorthodox ideas to save everything on Earth from extinction."]

### Case 3: A thoughtful story about memory and identity

Expected: matches; at least one memory/identity theme; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Memento** — 2000, 113 minutes, original language `en`; Mystery, Thriller.

Leonard Shelby is hunting for his wife’s killer while his rare short-term memory loss leaves him unable to remember what happened fifteen minutes ago, where he’s going, or why. That search for truth is tied directly to memory and identity as he tries to piece together his life after the accident.

Catalog overview: Leonard Shelby is tracking down the man who raped and murdered his wife. The difficulty of locating his wife's killer, however, is compounded by the fact that he suffers from a rare, untreatable form of short-term memory loss. Although he can recall details of life before his accident, Leonard cannot remember what happened fifteen minutes ago, where he's going, or why.

Server-resolved evidence: ["Leonard Shelby is tracking down the man who raped and murdered his wife.", "The difficulty of locating his wife's killer, however, is compounded by the fact that he suffers from a rare, untreatable form of short-term memory loss.", "Although he can recall details of life before his accident, Leonard cannot remember what happened fifteen minutes ago, where he's going, or why."]

**Eternal Sunshine of the Spotless Mind** — 2004, 108 minutes, original language `en`; Drama, Romance, Science Fiction.

Joel Barish chooses to erase his girlfriend from his memory after learning she did the same, but as the memories fade he realizes he still loves her and may be too late to undo his mistake. The story centers on memory, identity, and the emotional weight of trying to delete a relationship.

Catalog overview: Joel Barish, heartbroken that his girlfriend underwent a procedure to erase him from her memory, decides to do the same. However, as he watches his memories of her fade away, he realises that he still loves her, and may be too late to correct his mistake.

Server-resolved evidence: ["Joel Barish, heartbroken that his girlfriend underwent a procedure to erase him from her memory, decides to do the same.", "However, as he watches his memories of her fade away, he realises that he still loves her, and may be too late to correct his mistake."]

**The Bourne Identity** — 2002, 119 minutes, original language `en`; Action, Mystery, Thriller.

Amnesia and a single Swiss bank account number drive Jason Bourne’s search to reconstruct who he is, while the people he meets seem to want him dead. As he uncovers his own combat and mental skills, the story turns on memory, identity, and the question of who he really works for.

Catalog overview: Wounded to the brink of death and suffering from amnesia, Jason Bourne is rescued at sea by a fisherman. With nothing to go on but a Swiss bank account number, he starts to reconstruct his life, but finds that many people he encounters want him dead. However, Bourne realizes that he has the combat and mental skills of a world-class spy—but who does he work for?

Server-resolved evidence: ["Wounded to the brink of death and suffering from amnesia, Jason Bourne is rescued at sea by a fisherman.", "With nothing to go on but a Swiss bank account number, he starts to reconstruct his life, but finds that many people he encounters want him dead.", "However, Bourne realizes that he has the combat and mental skills of a world-class spy—but who does he work for?"]

### Case 5: A romantic comedy, no horror

Expected: matches; all Romance AND Comedy; no Horror; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Just Go with It** — 2011, 117 minutes, original language `en`; Comedy, Romance.

Danny Maccabee gets his loyal assistant Katherine to pose as his soon-to-be ex-wife to hide a lie while he’s romancing Palmer, and the mix-up grows when Katherine’s kids get pulled in too. The story then sends everyone to Hawaii for a weekend that shifts all their lives.

Catalog overview: While romancing Palmer, a much younger schoolteacher, plastic surgeon Danny Maccabee enlists his loyal assistant Katherine to pretend to be his soon to be ex-wife, in order to cover up a careless lie. When more lies backfire, Katherine's kids become involved, and everyone heads off for a weekend in Hawaii that will change all their lives.

Server-resolved evidence: ["While romancing Palmer, a much younger schoolteacher, plastic surgeon Danny Maccabee enlists his loyal assistant Katherine to pretend to be his soon to be ex-wife, in order to cover up a careless lie.", "When more lies backfire, Katherine's kids become involved, and everyone heads off for a weekend in Hawaii that will change all their lives."]

**Crazy, Stupid, Love.** — 2011, 118 minutes, original language `en`; Comedy, Drama, Romance.

After his seemingly perfect marriage falls apart when Emily wants a divorce, Cal is suddenly single and adrift in dating. Jacob Palmer then takes him under his wing and teaches him how to win with the ladies.

Catalog overview: Cal Weaver is living the American dream. He has a good job, a beautiful house, great children and a beautiful wife, named Emily. Cal's seemingly perfect life unravels, however, when he learns that Emily has been unfaithful and wants a divorce. Over 40 and suddenly single, Cal is adrift in the fickle world of dating. Enter, Jacob Palmer, a self-styled player who takes Cal under his wing and teaches him how to be a hit with the ladies.

Server-resolved evidence: ["Cal's seemingly perfect life unravels, however, when he learns that Emily has been unfaithful and wants a divorce.", "Over 40 and suddenly single, Cal is adrift in the fickle world of dating.", "Enter, Jacob Palmer, a self-styled player who takes Cal under his wing and teaches him how to be a hit with the ladies."]

**Lost in Translation** — 2003, 102 minutes, original language `en`; Comedy, Drama, Romance.

A young, neglected wife and a washed-up movie star cross paths in Tokyo and find an odd solace and pensive freedom in each other’s company, away from their lives in America. The story centers on their connection and the quiet, reflective space they create together.

Catalog overview: Two lost souls visiting Tokyo -- the young, neglected wife of a photographer and a washed-up movie star shooting a TV commercial -- find an odd solace and pensive freedom to be real in each other's company, away from their lives in America.

Server-resolved evidence: ["Two lost souls visiting Tokyo -- the young, neglected wife of a photographer and a washed-up movie star shooting a TV commercial -- find an odd solace and pensive freedom to be real in each other's company, away from their lives in America."]

### Case 7: A drama under 90 minutes

Expected: matches; all Drama; runtime strictly <90; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**The Iron Giant** — 1999, 86 minutes, original language `en`; Adventure, Animation, Drama, Family, Science Fiction.

A giant metal machine befriends a nine-year-old boy in Rockwell, Maine, and the story turns on its choice to save people from their own fears and prejudices. That gives you a story centered on an unusual friendship and a struggle against suspicion in a small town.

Catalog overview: In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices.

Server-resolved evidence: ["In the small town of Rockwell, Maine in October 1957, a giant metal machine befriends a nine-year-old boy and ultimately finds its humanity by unselfishly saving people from their own fears and prejudices."]

**Stand by Me** — 1986, 89 minutes, original language `en`; Adventure, Drama.

Four boys set out to see the body of a boy their age who has been accidentally killed near their rural homes, and the trip brings them face to face with a mean junk man, a marsh full of leeches, and hard truths about one another's very different home lives. What starts as a lark becomes a defining event in their lives.

Catalog overview: After learning that a boy their age has been accidentally killed near their rural homes, four boys decide to go see the body. Gordie, Vern, Chris, and Teddy encounter a mean junk man and a marsh full of leeches, but they also learn more about one another and their very different home lives. Just a lark at first, the boys' adventure evolves into a defining event in their lives.

Server-resolved evidence: ["After learning that a boy their age has been accidentally killed near their rural homes, four boys decide to go see the body.", "Gordie, Vern, Chris, and Teddy encounter a mean junk man and a marsh full of leeches, but they also learn more about one another and their very different home lives.", "Just a lark at first, the boys' adventure evolves into a defining event in their lives."]

**Grave of the Fireflies** — 1988, 89 minutes, original language `ja`; Animation, Drama, War.

Orphaned in the final months of World War II, Seita and his younger sister Setsuko are forced into an abandoned bomb shelter after a falling out with their aunt. With no surviving relatives and their rations gone, the story follows their struggle to survive.

Catalog overview: In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan. After a falling out with their aunt, they move into an abandoned bomb shelter. With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive.

Server-resolved evidence: ["In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan.", "After a falling out with their aunt, they move into an abandoned bomb shelter.", "With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive."]

### Case 9: A science fiction film released from 2010 through 2020

Expected: matches; all Science Fiction; 2010<=year<=2020; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Transcendence** — 2014, 119 minutes, original language `en`; Drama, Mystery, Science Fiction, Thriller.

Two leading computer scientists pursue Technological Singularity while a radical anti-technology organization tries to stop them from creating a world where computers can transcend the human brain. It centers on that clash between advanced technology and organized resistance.

Catalog overview: Two leading computer scientists work toward their goal of Technological Singularity,  as a radical anti-technology organization fights to prevent them from creating a world where computers can transcend the abilities of the human brain.

Server-resolved evidence: ["Two leading computer scientists work toward their goal of Technological Singularity,  as a radical anti-technology organization fights to prevent them from creating a world where computers can transcend the abilities of the human brain."]

**Ad Astra** — 2019, 123 minutes, original language `en`; Drama, Science Fiction.

A mysterious phenomenon threatens Earth, and astronaut Roy McBride travels across deep space to uncover the truth about a lost expedition that vanished into emptiness and silence. The story centers on perilous space travel, a threatened planet, and a search for what happened to the earlier mission.

Catalog overview: The near future, a time when both hope and hardships drive humanity to look to the stars and beyond. While a mysterious phenomenon menaces to destroy life on planet Earth, astronaut Roy McBride undertakes a mission across the immensity of space and its many perils to uncover the truth about a lost expedition that decades before boldly faced emptiness and silence in search of the unknown.

Server-resolved evidence: ["The near future, a time when both hope and hardships drive humanity to look to the stars and beyond.", "While a mysterious phenomenon menaces to destroy life on planet Earth, astronaut Roy McBride undertakes a mission across the immensity of space and its many perils to uncover the truth about a lost expedition that decades before boldly faced emptiness and silence in search of the unknown."]

**Godzilla** — 2014, 123 minutes, original language `en`; Action, Drama, Science Fiction.

Ford Brody is pulled from a family reunion in San Francisco into a crisis in Japan, where he and his estranged father get swept up as an ancient sea-born predator rises and the creatures race toward a final battleground in San Francisco. The story centers on that escalating struggle around humanity’s survival and the destruction left in the creatures’ wake.

Catalog overview: Ford Brody, a Navy bomb expert, has just reunited with his family in San Francisco when he is forced to go to Japan to help his estranged father, Joe. Soon, both men are swept up in an escalating crisis when an ancient alpha predator arises from the sea to combat malevolent adversaries that threaten the survival of humanity. The creatures leave colossal destruction in their wake, as they make their way toward their final battleground: San Francisco.

Server-resolved evidence: ["Ford Brody, a Navy bomb expert, has just reunited with his family in San Francisco when he is forced to go to Japan to help his estranged father, Joe.", "Soon, both men are swept up in an escalating crisis when an ancient alpha predator arises from the sea to combat malevolent adversaries that threaten the survival of humanity.", "The creatures leave colossal destruction in their wake, as they make their way toward their final battleground: San Francisco."]

### Case 11: A Japanese animated film

Expected: matches; all Animation; original_language ja; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Spirited Away** — 2001, 125 minutes, original language `ja`; Animation, Family, Fantasy.

Chihiro gets trapped in a strange world of spirits, and after her parents are mysteriously transformed, she has to find courage she didn’t know she had to rescue her family.

Catalog overview: A young girl, Chihiro, becomes trapped in a strange new world of spirits. When her parents undergo a mysterious transformation, she must call upon the courage she never knew she had to free her family.

Server-resolved evidence: ["A young girl, Chihiro, becomes trapped in a strange new world of spirits.", "When her parents undergo a mysterious transformation, she must call upon the courage she never knew she had to free her family."]

**Grave of the Fireflies** — 1988, 89 minutes, original language `ja`; Animation, Drama, War.

Set in the final months of World War II, it follows 14-year-old Seita and his sister Setsuko after their mother is killed in an air raid, then as they move into an abandoned bomb shelter and struggle to survive with no surviving relatives and depleted rations.

Catalog overview: In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan. After a falling out with their aunt, they move into an abandoned bomb shelter. With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive.

Server-resolved evidence: ["In the final months of World War II, 14-year-old Seita and his sister Setsuko are orphaned when their mother is killed during an air raid in Kobe, Japan.", "After a falling out with their aunt, they move into an abandoned bomb shelter.", "With no surviving relatives and their emergency rations depleted, Seita and Setsuko struggle to survive."]

**Princess Mononoke** — 1997, 134 minutes, original language `ja`; Adventure, Animation, Fantasy.

Ashitaka, a cursed prince, travels west to seek a cure and gets pulled into a clash between San, who fights to protect the forest, and Lady Eboshi, who wants to destroy it. The story centers on his effort to bring balance to that conflict.

Catalog overview: Ashitaka, a prince of the disappearing Emishi people, is cursed by a demonized boar god and must journey to the west to find a cure. Along the way, he encounters San, a young human woman fighting to protect the forest, and Lady Eboshi, who is trying to destroy it. Ashitaka must find a way to bring balance to this conflict.

Server-resolved evidence: ["Ashitaka, a prince of the disappearing Emishi people, is cursed by a demonized boar god and must journey to the west to find a cure.", "Along the way, he encounters San, a young human woman fighting to protect the forest, and Lady Eboshi, who is trying to destroy it.", "Ashitaka must find a way to bring balance to this conflict."]

### Case 14: A drama starring Tom Hanks

Expected: matches with visible actor unchecked warning; no casting claim; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

**Captain Phillips** — 2013, 134 minutes, original language `en`; Action, Drama, Thriller.

The film centers on Captain Richard Phillips during the 2009 hijacking of the US-flagged MV Maersk Alabama by Somali pirates, telling the true story of a cargo ship crisis at sea. The requested Tom Hanks detail is missing from the supplied catalog facts, so I can only describe the story itself.

Catalog overview: The true story of Captain Richard Phillips and the 2009 hijacking by Somali pirates of the US-flagged MV Maersk Alabama, the first American cargo ship to be hijacked in two hundred years.

Server-resolved evidence: ["The true story of Captain Richard Phillips and the 2009 hijacking by Somali pirates of the US-flagged MV Maersk Alabama, the first American cargo ship to be hijacked in two hundred years."]

**Saving Private Ryan** — 1998, 169 minutes, original language `en`; Drama, History, War.

Three brothers are already dead on the battlefield, with a fourth trapped behind enemy lines, and Ranger captain John Miller leads seven men into German-held territory to bring him home. The requested detail about Tom Hanks is missing from the supplied catalog data, so I can only describe the rescue mission from the overview.

Catalog overview: As U.S. troops storm the beaches of Normandy, three brothers lie dead on the battlefield, with a fourth trapped behind enemy lines. Ranger captain John Miller and seven men are tasked with penetrating German-held territory and bringing the boy home.

Server-resolved evidence: ["troops storm the beaches of Normandy, three brothers lie dead on the battlefield, with a fourth trapped behind enemy lines.", "Ranger captain John Miller and seven men are tasked with penetrating German-held territory and bringing the boy home."]

**(500) Days of Summer** — 2009, 95 minutes, original language `en`; Comedy, Drama, Romance.

Tom, a greeting-card writer and hopeless romantic, is suddenly dumped by Summer and spends the next 500 days looking back at where their relationship went wrong while rediscovering his true passions. The requested detail about Tom Hanks is missing because the supplied catalog data does not list cast information.

Catalog overview: Tom, greeting-card writer and hopeless romantic, is caught completely off-guard when his girlfriend, Summer, suddenly dumps him. He reflects on their 500 days together to try to figure out where their love affair went sour, and in doing so, Tom rediscovers his true passions in life.

Server-resolved evidence: ["Tom, greeting-card writer and hopeless romantic, is caught completely off-guard when his girlfriend, Summer, suddenly dumps him.", "He reflects on their 500 days together to try to figure out where their love affair went sour, and in doing so, Tom rediscovers his true passions in life."]

### Case 19: A movie in English or French; I have not decided which original language

Expected: matches; original_languages [en, fr] with OR semantics; no clarification solely for alternative languages; every returned movie is English or French; all returned cards have completed grounded explanations in this bounded sample; natural direct wording with no generic fit verdicts.

Interpreted allowed languages: `["en", "fr"]`. No clarification requested.

**Scary Movie** — 2000, 88 minutes, original language `en`; Comedy.

A group of teenagers is stalked by a masked killer, and the film keeps layering in satire as the victims pile up. The story is built as an outrageously funny parody of familiar scary movies.

Catalog overview: A familiar-looking group of teenagers find themselves being stalked by a more-than-vaguely recognizable masked killer! As the victims begin to pile up and the laughs pile on, none of your favorite scary movies escape the razor-sharp satire of this outrageously funny parody!

Server-resolved evidence: ["A familiar-looking group of teenagers find themselves being stalked by a more-than-vaguely recognizable masked killer!", "As the victims begin to pile up and the laughs pile on, none of your favorite scary movies escape the razor-sharp satire of this outrageously funny parody!"]

**La La Land** — 2016, 129 minutes, original language `en`; Comedy, Drama, Romance.

Mia is an aspiring actress juggling auditions and service work while Sebastian struggles as a jazz musician in dingy bars, and their relationship starts to fray as success brings choices that pull their shared dreams apart.

Catalog overview: Mia, an aspiring actress, serves lattes to movie stars in between auditions and Sebastian, a jazz musician, scrapes by playing cocktail party gigs in dingy bars, but as success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair, and the dreams they worked so hard to maintain in each other threaten to rip them apart.

Server-resolved evidence: ["Mia, an aspiring actress, serves lattes to movie stars in between auditions and Sebastian, a jazz musician, scrapes by playing cocktail party gigs in dingy bars, but as success mounts they are faced with decisions that begin to fray the fragile fabric of their love affair, and the dreams they worked so hard to maintain in each other threaten to rip them apart."]

**Once Upon a Time in… Hollywood** — 2019, 162 minutes, original language `en`; Comedy, Drama, Thriller.

Set in Los Angeles in 1969, the story follows TV star Rick Dalton and his stuntman friend Cliff Booth as they try to survive a changing movie industry, while Dalton lives next door to Sharon Tate, a young actress and model who has just married Roman Polanski.

Catalog overview: Los Angeles, 1969. TV star Rick Dalton, a struggling actor specializing in westerns, and stuntman Cliff Booth, his best friend, try to survive in a constantly changing movie industry. Dalton is the neighbor of the young and promising actress and model Sharon Tate, who has just married the prestigious Polish director Roman Polanski…

Server-resolved evidence: ["Los Angeles, 1969.", "TV star Rick Dalton, a struggling actor specializing in westerns, and stuntman Cliff Booth, his best friend, try to survive in a constantly changing movie industry.", "Dalton is the neighbor of the young and promising actress and model Sharon Tate, who has just married the prestigious Polish director Roman Polanski…"]
