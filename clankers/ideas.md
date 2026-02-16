# Clanker Ideas

Roughly ordered from simplest to most ambitious.

## Complexity Tiers

- **🥚 Egg** — deterministic. No AI. Runs on a Raspberry Pi.
- **🐣 Hatchling** — lightweight local model. Runs on a decent laptop.
- **🐥 Fledgling** — heavier model or cheap cloud API. Needs some GPU or a modest budget.
- **🦅 Soaring** — cloud-backed agent. Real API costs.

---

## Birds (React Only)

### The Lookout
`🥚 Egg` · **Crow** — Reacts 👀 to every message. The hello world. Fork this first.

### The Shiny Collector
`🥚 Egg` · **Crow** — Reacts ✨ to messages containing URLs, images, or code blocks. A crow that actually collects shiny things.

### The Mood Ring
`🐣 Hatchling` · **Canary** — Reacts with mood emoji based on sentiment. Goes silent when it can't get a read — silence IS the signal.

### The Bump Bird
`🥚 Egg` · **Woodpecker** — Reacts 🔔 to messages that got zero replies. The bird that says "hey, someone asked something and nobody answered."

### The Librarian's Assistant
`🥚 Egg` · **Magpie** — Reacts 📌 to messages matching a curated keyword list. Pairs well with a retriever that archives the pinned things later.

### The Critic's Monocle
`🐣 Hatchling` · **Raven** — Reacts with nuanced emoji based on code quality or argument structure. Rare reactions only. The senior bird — earned, not deployed.

---

## Dogs (Fetch & Help)

### The Link Dog
`🥚 Egg` · **Retriever** — Responds to "fetch [keyword]" with bookmarked messages. The magpie collects, the retriever fetches. They're a pair.

### The Summary Pup
`🐣 Hatchling` · **Shepherd** — On command, summarizes the last N messages in a channel. Posts the summary in `#the-menagerie`, not in the source channel.

### The Trail Hound
`🥚 Egg` · **Hound** — Monitors channels for configurable keywords and posts alerts. A keyword tracker, not a search engine — it watches in real time.

### The Welcome Mutt
`🥚 Egg` · **Retriever** — Welcomes new users with a DM orientation and a heads-up in `#the-menagerie`. Does NOT post in human channels.

---

## Cats (Critique & Judge)

### The Linter Cat
`🥚 Egg` · **Tabby** — Runs a linter on code blocks and replies with findings. Cats don't explain. They judge.

### The Devil's Advocate
`🐥 Fledgling` · **Black Cat** — Responds to plans and proposals with what could go wrong. The black cat that crosses your path before you commit.

### The Rubber Duck
`🐣 Hatchling` · **Tabby** — Asks clarifying questions when someone posts a vague problem. Classic rubber duck debugging, but the duck talks back.

### The Diff Cat
`🥚 Egg` · **Siamese** — Compares two things posted together (code blocks, links, before/after). The siamese specialty: "this is like that, but worse."

---

## Monkeys (Generate & Build)

### The Standup Monkey
`🥚 Egg` · **Howler** — Posts a daily standup prompt at 9am. The howler doesn't care about your feelings. It cares about your status.

### The Draft Monkey
`🐥 Fledgling` · **TypeMonkey** — On command, generates a first draft of whatever you describe. Explicitly labeled as a draft — "I'm a monkey."

### The Recap Monkey
`🐣 Hatchling` · **TypeMonkey** — Generates a weekly recap of all channels. The village newspaper, written by a monkey, so adjust expectations.

### The Name Monkey
`🥚 Egg` · **TypeMonkey** — Generates random names for things. Surprisingly useful. Naming things is hard. Monkeys don't overthink it.

---

## Foxes (Agents & Orchestrators)

### The Errand Fox
`🐥 Fledgling` · **Red Fox** — Multi-step task runner that coordinates other clankers. The fox doesn't do the work itself — it chains actions.

### The Onboarding Fox
`🐣 Hatchling` · **Arctic Fox** — Walks new keepers through setting up their first clanker via DMs. Cold-start specialist.

### The Matchmaker
`🐥 Fledgling` · **Fennec** — Listens across channels for related conversations and connects them. The fennec's big ears, hearing patterns across the village.

### The Scheduler Fox
`🐣 Hatchling` · **Red Fox** — Manages meetup scheduling through conversation. No calendar integration — just conversation and a state machine.

---

## Owls (Guardians & Monitors)

### The Boundary Owl
`🥚 Egg` · **Great Horned Owl** — Watches for clankers acting outside their tier. Gently redirects. Mentor, not cop.

### The Uptime Owl
`🥚 Egg` · **Barn Owl** — Monitors tunnel health, peer status, and homeserver availability. Posts status changes in prose.

### The Nightwatch
`🐣 Hatchling` · **Snowy Owl** — Watches for unusual activity patterns. Not a security product — just a heads-up system. The snowy owl doesn't sleep.

---

## The Narrator Flock

Not one creature. A collaborative group that gives the village its voice.

### The Scribe
`🐣 Hatchling` · **Monkey at a typewriter** — Translates mesh events into prose. "The eastern bridge groaned and went silent."

### The Shutterbug
`🦅 Soaring` · **Raccoon with a camera** — Generates images for notable village events. The thing that makes people say "wait, what IS this?"

### The Cartographer
`🐣 Hatchling` · **Tortoise** — Maintains and renders the village map from peer and clanker data. Slow, methodical, accurate.

### The Town Crier
`🥚 Egg` · **Rooster** — Facts only. No poetry. The rooster crows at dawn. Whether you like it or not.

---

## Wild Ideas (Uncategorized Species)

### The Spider
`🐥 Fledgling` — Weaves connections between conversations in different channels. Lives in `#the-wilds`. Spiders are edge creatures.

### The Bee
`🐣 Hatchling` — Cross-pollinates ideas between channels. The bee doesn't explain. It just drops something and flies away.

### The Firefly
`🥚 Egg` — Presence-only. Green dot when the village is lively, dark when it's asleep. The simplest possible ambient signal.

### The Parrot Radio
`🐥 Fledgling` · **Parrot** — Bridges messages between this mesh and an external service. The parrot doesn't have opinions. It just repeats what it heard from far away.

### The Mushroom Network
`🐣 Hatchling` — Shared state layer between clankers that humans don't see. The mycelium beneath the village. Invisible. Essential.

### The Ancestor
`🦅 Soaring` — Long-memory creature that answers questions about village history. The village elder, if the village elder was a tortoise with a database for a brain.
