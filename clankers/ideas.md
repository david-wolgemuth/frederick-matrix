# Clanker Ideas

Roughly ordered from simplest to most ambitious. Each idea includes a complexity tier, what it actually does, and what creature it wants to be.

## Complexity Tiers

- **🥚 Egg** — deterministic. No AI. Regex, cron jobs, API calls. Runs on a Raspberry Pi.
- **🐣 Hatchling** — lightweight local model. Ollama, small LLM, local embeddings. Runs on a decent laptop.
- **🐥 Fledgling** — heavier local model or cheap cloud API. Needs some GPU or a modest API budget.
- **🦅 Soaring** — cloud-backed agent. Tool use, multi-step reasoning, image generation. Real API costs.

---

## Birds (React Only)

### The Lookout
`🥚 Egg` · **Crow**

Reacts 👀 to every message. The hello world. The boilerplate. Fork this first.

- Deterministic: listen to room events, send reaction, done
- Maybe 20 lines of code
- The only value is "I saw this" — and that's enough to start

### The Shiny Collector
`🥚 Egg` · **Crow**

Reacts ✨ to messages containing URLs, images, or code blocks. Ignores plain text.

- Regex detection: links, fenced code, image events
- Different emoji for different content: 🔗 links, 💻 code, 🖼️ images
- A crow that actually collects shiny things

### The Mood Ring
`🐣 Hatchling` · **Canary**

Reacts with mood emoji based on message sentiment.

- Local sentiment model (VADER, or a tiny classifier via Ollama)
- 😊 positive, 😐 neutral, 😟 negative, 🔥 heated
- Goes silent when it can't get a read — silence IS the signal
- The canary in the coal mine: if it stops reacting, check the vibe

### The Bump Bird
`🥚 Egg` · **Woodpecker**

Reacts 🔔 to messages older than N hours that got zero replies and zero reactions.

- Cron job: scan recent messages, find orphans, tap them
- Simple heuristic: questions (contains `?`) get priority
- The bird that says "hey, someone asked something and nobody answered"

### The Librarian's Assistant
`🥚 Egg` · **Magpie**

Reacts 📌 to messages that contain keywords matching a curated list (project names, recurring topics, action items).

- Keyword list in a config file, updated by the keeper
- Could also react to messages that get 3+ reactions from others (popular = worth saving)
- Pairs well with a dog that actually archives the pinned things later

### The Critic's Monocle
`🐣 Hatchling` · **Raven**

Reacts with nuanced emoji based on code quality, argument structure, or factual claims.

- Local model evaluates message content
- 🎯 strong point, 🤔 questionable, ⚡ clever, 🧱 solid but boring
- Rare reactions — only triggers on substantial messages
- The senior bird. Earned, not deployed.

---

## Dogs (Fetch & Help)

### The Link Dog
`🥚 Egg` · **Retriever**

Responds to "fetch [keyword]" in `#the-menagerie`. Searches a local index of bookmarked messages (from the magpie's reactions) and returns the top result.

- SQLite index of messages the magpie flagged
- Simple keyword search, returns message link + preview
- The magpie collects, the retriever fetches. They're a pair.

### The Summary Pup
`🐣 Hatchling` · **Shepherd**

On command, summarizes the last N messages in a channel.

- "shepherd, what happened in #beans-and-bagels today?"
- Local model (Ollama, small Llama/Mistral) generates a 2-3 sentence summary
- Posts summary in `#the-menagerie`, not in the source channel
- Useful for people catching up after being away

### The Trail Hound
`🥚 Egg` · **Hound**

Monitors channels for configurable keywords/patterns and posts alerts in `#the-menagerie`.

- Config file: `{"track": ["deploy", "outage", "help", "TODO"]}`
- When triggered: posts "🐕 Caught a scent in #tech-quarter: [message preview]"
- Keyword tracker, not a search engine — it watches in real time

### The Welcome Mutt
`🥚 Egg` · **Retriever**

When a new user joins, posts a friendly welcome in `#the-menagerie` and DMs them a quick orientation.

- Watches `m.room.member` events for new joins
- DM: "Welcome to the village. Here's how things work: [link to docs]"
- Posts in menagerie: "🐕 A new face at the gate. Say hello."
- Does NOT post in human channels — the welcome is private + creature-space

---

## Cats (Critique & Judge)

### The Linter Cat
`🥚 Egg` · **Tabby**

When someone posts a code block in `#the-menagerie` or `#the-kennel`, runs a linter and replies with findings.

- Detects language from fenced code block syntax
- Runs `ruff` (Python), `eslint` (JS), `clippy` (Rust) in a sandbox
- Terse output: "🐈 3 issues. Missing type hint L4. Unused import L1. Line too long L12."
- Cats don't explain. They judge.

### The Devil's Advocate
`🐥 Fledgling` · **Black Cat**

Responds to plans and proposals with what could go wrong.

- Trigger: messages containing "plan", "proposal", "idea", "what if we", "I'm thinking"
- Local or cheap cloud model generates 2-3 risks/concerns
- "🐈‍⬛ What if the tunnel goes down mid-demo? What if nobody shows up? What if the API rate-limits you?"
- The black cat that crosses your path before you commit

### The Rubber Duck
`🐣 Hatchling` · **Tabby**

Asks clarifying questions when someone posts a vague problem.

- Detects question-like messages that lack specifics
- "🐈 What error message? What did you expect? What changed since it last worked?"
- Not solving the problem — just making you state it properly
- Classic rubber duck debugging, but the duck talks back

### The Diff Cat
`🥚 Egg` · **Siamese**

When someone posts two things (two links, two code blocks, a before/after), generates a comparison.

- Detects paired content in a message
- Runs `diff`, or for links, fetches and compares
- "🐈 These are mostly the same. Key differences: [terse summary]"
- The siamese specialty: "this is like that, but worse"

---

## Monkeys (Generate & Build)

### The Standup Monkey
`🥚 Egg` · **Howler**

Posts a daily standup prompt in `#the-menagerie` at 9am.

- Cron job: "🐒📢 MORNING. What are you working on? What's blocking you?"
- Optional: collects replies in-thread and posts a summary at EOD
- The howler doesn't care about your feelings. It cares about your status.

### The Draft Monkey
`🐥 Fledgling` · **TypeMonkey**

On command, generates a first draft of whatever you describe.

- "typemonkey, draft a meetup description for Thursday at District Arts"
- Cloud or local model generates a rough draft
- Posts in-thread in `#the-menagerie`
- Explicitly labeled as a draft — "🐒 FIRST DRAFT. Edit heavily. I'm a monkey."

### The Recap Monkey
`🐣 Hatchling` · **TypeMonkey**

Generates a weekly recap of all channels, posted every Sunday night.

- Pulls message history from all readable channels
- Local model summarizes each channel's week in 2-3 sentences
- Posts a single threaded message in `#the-menagerie`
- The village newspaper, written by a monkey, so adjust expectations accordingly

### The Name Monkey
`🥚 Egg` · **TypeMonkey**

Generates random names for things. Channels, events, projects, other clankers.

- "namemonkey, name my new crow" → "🐒 How about: Soot, Glint, Pebble, Rook, Smudge"
- Markov chain or wordlist mashup, no AI needed
- Surprisingly useful. Naming things is hard. Monkeys don't overthink it.

---

## Foxes (Agents & Orchestrators)

### The Errand Fox
`🐥 Fledgling` · **Red Fox**

Multi-step task runner. Breaks down a request and chains actions.

- "fox, find that article about Matrix federation, summarize it, and post it in #tech-quarter"
- Calls the hound (search) → fetches the link → calls the shepherd (summarize) → posts result
- The fox doesn't do the work itself — it coordinates other clankers
- Requires: tool-use capable model, awareness of available clankers

### The Onboarding Fox
`🐣 Hatchling` · **Arctic Fox**

Walks new keepers through setting up their first clanker.

- Interactive conversation in DMs
- "What kind of creature do you want to build? Let's start with a crow."
- Generates a pre-configured `.env` file based on their answers
- Cold-start specialist: thrives when everything is new

### The Matchmaker
`🐥 Fledgling` · **Fennec**

Listens across channels for related conversations happening in different rooms and connects them.

- Embeddings-based similarity between recent messages in different channels
- "🦊 Heads up — @alice in #tech-quarter and @bob in #beans-and-bagels are both talking about DNS issues. Might want to compare notes."
- The fennec's big ears, hearing patterns across the village

### The Scheduler Fox
`🐣 Hatchling` · **Red Fox**

Manages meetup scheduling through conversation.

- "fox, find a time for 4 people to meet at District Arts next week"
- Collects availability via DMs or thread replies
- Proposes options, handles conflicts
- Posts confirmed event in the appropriate channel
- No calendar integration needed — just conversation and a state machine

---

## Owls (Guardians & Monitors)

### The Boundary Owl
`🥚 Egg` · **Great Horned Owl**

The community moderator. Watches for clankers acting outside their tier.

- Knows which accounts are clankers (from `clankers.json`)
- Knows which channels are `#the-*` (clanker territory) vs real places
- Gently redirects: "🦉 Hey @keeper — your crow wandered into the coffee shop."
- Escalates to DM on repeat, temporary mute only as last resort
- Mentor, not cop. First clanker you actually need.

### The Uptime Owl
`🥚 Egg` · **Barn Owl**

Monitors tunnel health, peer status, and homeserver availability.

- Periodic health checks against Synapse, tunnel URL, peer `server.json` endpoints
- Posts status changes in `#the-menagerie`: "🦉 The eastern bridge is open." / "🦉 Fog on the eastern bridge."
- Also feeds events to the narrator flock for prose generation
- Basically `make status` running on a cron, with a personality

### The Nightwatch
`🐣 Hatchling` · **Snowy Owl**

Watches for unusual patterns. Not a security product — just a heads-up system.

- Anomaly detection: sudden message volume spikes, new accounts posting rapidly, repeated failed actions
- "🦉 Unusual activity from @unknown-user-47. 30 messages in 2 minutes. Might be a misconfigured bot."
- Local heuristics, no cloud needed
- The snowy owl doesn't sleep. It just watches.

---

## The Narrator Flock

Not one creature. A collaborative group that gives the village its voice.

### The Scribe
`🐣 Hatchling` · **Monkey at a typewriter**

Translates mesh events into prose in `#the-commons`.

- Watches: tunnel up/down, peer online/offline, user joins/leaves, clanker deployed
- Mapping table of events to prose templates with randomized phrasing
- "The eastern bridge groaned and went silent." / "Smoke rises from a new chimney to the north."
- Multiple scribes can run with different styles — poetic, terse, comic, ominous

### The Shutterbug
`🦅 Soaring` · **Raccoon with a camera** (or beetle with a lens eye)

Generates images for notable village events.

- Tunnel comes up → watercolor of a misty bridge clearing
- New peer → sketch of distant chimney smoke
- Stable Diffusion / SDXL / DALL-E, triggered by the same events the scribe watches
- Posts images in `#the-commons` alongside the prose
- The crowd-pleaser. The thing that makes people say "wait, what IS this?"

### The Cartographer
`🐣 Hatchling` · **Tortoise** (or spider)

Maintains and renders the village map.

- Reads `peers.json` and `clankers.json` from all nodes
- Generates an SVG or updates `map.json` with settlement positions, roads, fauna
- Posts updated map in `#the-commons` when topology changes
- Slow, methodical, accurate. Tortoise energy.

### The Town Crier
`🥚 Egg` · **Rooster**

The blunt version. Facts only. No poetry.

- "🐓 TUNNEL UP 14:32. PEER alice ONLINE. 12 MESSAGES TODAY. 3 CLANKERS ACTIVE."
- For people who want signal, not narrative
- Cron-based daily digest or event-triggered one-liners
- The rooster crows at dawn. Whether you like it or not.

---

## Wild Ideas (Uncategorized Species)

### The Spider
`🐥 Fledgling`

Weaves connections between threads. When a conversation in one channel references or overlaps with a conversation in another, the spider spins a thread between them.

- Embedding similarity across channels
- Posts: "🕷️ A thread connects this to [link in other channel]"
- Lives in `#the-wilds`. Spiders are edge creatures.

### The Bee
`🐣 Hatchling`

Cross-pollinates ideas. Picks up interesting fragments from one channel and deposits them in another where they might be relevant.

- "🐝 Pollen from #tech-quarter: someone mentioned [topic]. Might be relevant here."
- Gentle, opt-in, low frequency
- The bee doesn't explain. It just drops something and flies away.

### The Firefly
`🥚 Egg`

Glows when something is happening. A presence-only bot that sets its Matrix presence to "active" when the village is lively and "idle" when it's quiet.

- No messages. No reactions. Just a green dot in the member list that pulses with village activity.
- If you see the firefly glowing, people are around. If it's dark, the village is asleep.
- The simplest possible ambient signal.

### The Parrot Radio
`🐥 Fledgling` · **Parrot**

Bridges messages between this mesh and an external service (Discord, Slack, IRC, RSS feed).

- Matrix ↔ external platform bridge, wearing a parrot skin
- "🦜 [from Discord] hey is the meetup still on Thursday?"
- The parrot doesn't have opinions. It just repeats what it heard from far away.

### The Mushroom Network
`🐣 Hatchling`

Underground communication between clankers. A shared state layer that bots read/write but humans don't see.

- Custom Matrix state events in a hidden room
- Clankers post observations: "saw a link about X", "vibe in #general is heated", "3 unanswered questions"
- Other clankers read this shared state and act on it
- The mycelium beneath the village. Invisible. Essential.

### The Ancestor
`🦅 Soaring`

A long-memory creature that remembers everything. Answers questions about village history.

- "ancestor, when did we first talk about federation?"
- "ancestor, who deployed the first canary?"
- Full message archive + RAG pipeline + local or cloud LLM
- Speaks slowly. Knows everything. The village elder, if the village elder was a tortoise with a database for a brain.
