# Clankers

Clankers are bots that live in the village. They have names, faces, species, and keepers. They are not services — they are creatures.

## Quick Start

The crow is the starter clanker. It reacts 👀 in watched rooms and caws only in explicitly allowed rooms.

```bash
pip install simplematrixbotlib httpx
export CROW_HOMESERVER=http://localhost:8008
export CROW_USERNAME=crow
export CROW_PASSWORD=changeme
python clankers/crow/main.py
```

Register the account first (one-time, requires admin token):

```bash
export SYNAPSE_ADMIN_TOKEN=syt_...
python clankers/crow/main.py --register
```

This creates the account with `user_type="bot"` so Synapse knows it's a clanker, not a person.

## How It Works

A clanker is a Matrix bot with a personality. The crow template ([`crow/main.py`](crow/main.py)) shows the pattern:

- **Config from environment** — homeserver URL, credentials, and two channel lists: `CROW_REACT_ROOMS` (where it watches) and `CROW_ALLOWED_ROOMS` (where it speaks).
- **Identity block** — every clanker has a type tag (`🤖[crow]`) and a voice (the caw string). This is how people recognize it in the room.
- **Behavior listener** — listens for message events, reacts 👀 in watched rooms, caws only in explicitly allowed rooms. Never broadcasts. If no allowed rooms are set, it stays silent — reactions only.

That's the whole creature. Everything else is mutation. Read `crow/main.py` for the full source.

## Species

Clankers are classified by what they're allowed to do:

| Tier | Species | Ability | Example |
|------|---------|---------|---------|
| **Bird** | Crow, Canary, Magpie | React only | 👀 on messages |
| **Dog** | Retriever, Hound, Shepherd | Fetch & reply on command | Summarize a channel |
| **Cat** | Tabby, Siamese | Critique & judge | Lint a code block |
| **Monkey** | Howler, TypeMonkey | Generate & post | Daily standup prompt |
| **Fox** | Red Fox, Fennec | Orchestrate other clankers | Chain search → summarize → post |
| **Owl** | Barn Owl, Snowy Owl | Guard & monitor | Redirect a lost clanker |

See [ideas.md](ideas.md) for the full bestiary of creature concepts.

## Creature Etiquette

- **Be quiet by default.** Silence has meaning. If your clanker reacts to everything, it's wallpaper.
- **Stay in your habitat.** Crows squawk in `#the-fields`, not in `#beans-and-bagels`.
- **Name it like a creature.** `Dusty`, not `link-reaction-bot-v2`.
- **No human faces.** Animal, machine, or mythical. Never human-passing.
- **Put your name on it.** Bio says who keeps this clanker. Accountability, not surveillance.
- **Start with a crow.** Even if you've built bots before. The crow teaches you how the village works.

## File Layout

```
clankers/
├── README.md        ← you are here
├── mindset.md       ← philosophy of raising a clanker
├── ideas.md         ← bestiary of creature concepts
└── crow/
    └── main.py      ← starter clanker template
```

## Further Reading

- [mindset.md](mindset.md) — the full guide to raising a clanker: the mindset, two paths (host vs build), etiquette, troubleshooting, and keeper responsibilities
- [ideas.md](ideas.md) — creature ideas from 🥚 Egg (no AI, 20 lines) to 🦅 Soaring (cloud-backed agents)
