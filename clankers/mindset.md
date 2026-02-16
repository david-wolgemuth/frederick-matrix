# Raising a Clanker

## The Mindset

You are not deploying a bot. You are releasing a creature into a village.

It will have a name, a face, a species, and a temperament. It will be seen by other people in the channels it inhabits. It will react to things, maybe say things, and over time it will become part of the texture of the community. People will recognize it. They'll say "oh, that's Dave's crow" or "the canary's been quiet today, is something wrong?"

This is not a technical decision. It's a social one. You're introducing a new resident.

Think about:

- **What does the village need?** Not what's technically interesting to build. Walk around the channels first. Are questions going unanswered? Is the vibe off? Are links getting lost? Are people posting into silence? The best clanker fills a gap that's already there.

- **What creature fits?** A retriever for a channel where people keep asking "does anyone have that link?" A canary for a space where tone matters. A crow for a busy channel where things scroll past too fast. The species isn't cosmetic — it tells people what to expect.

- **How loud should it be?** Most clankers should be quieter than you think. A bird that reacts to one in ten messages is more interesting than one that reacts to everything. Silence has meaning in the village. If your clanker is always making noise, it becomes wallpaper. If it's usually quiet and then suddenly reacts — people notice.

- **Would you want this creature in the room?** Sit in the channel. Imagine your clanker doing its thing while you're trying to have a conversation. Is it adding something? Or is it a pigeon shitting on the table? Be honest.

## The Vision

The village is not a platform. It's not a hackathon. It's a community that happens to be built on Matrix, running on homeservers in people's apartments, connected by ephemeral tunnels.

The clankers make it alive. Not because they're smart or powerful, but because they create the feeling that the village is inhabited — that things are happening even when you're not looking, that someone (or something) noticed what you said, that the space has texture beyond the last human message.

A good clanker is like a good neighbor. You don't need to interact with it every day. But you'd notice if it was gone.

## Two Paths

### Path 1: Host an Existing Clanker

Someone has already built a clanker and published the template. You're giving it a home on your machine and a unique identity in the village. This is the fast path. You can have a creature running in minutes.

**What you're doing:**
- Running someone else's code on your machine
- Registering a new Matrix account for it
- Giving it a unique name, avatar, and bio
- Pointing it at your homeserver and the right channels

**What you're NOT doing:**
- Writing code (unless you want to tweak behavior)
- Designing the creature from scratch
- Reinventing anything

**Steps:**

1. **Pick a template.** Browse the clanker templates in the repo. Start with the crow — it's the boilerplate, the "hello world," the creature every keeper raises first.

2. **Register an account.** Ask your node admin for a registration token. Register a new account for the clanker — this is its own identity, separate from yours.

   ```
   # get a token from admin
   # register at your node's Element, or via API:
   curl -X POST https://<your-homeserver>/_matrix/client/v3/register \
     -d '{"username": "dusty-crow", "password": "...", "auth": {"type": "m.login.token", ...}}'
   ```

3. **Name it.** Not "crow-bot-1." Give it a real name. Dusty. Glint. Pebble. Soot. The name should feel like a creature, not a deployment.

4. **Give it a face.** Set an avatar. It must be an animal, creature, or machine — never human-passing. Pixel art, hand-drawn, generated, whatever — but it should look like it belongs in the village. Bonus points for visible clockwork, a gear, a lens eye, something that says "I'm a clanker."

5. **Write its bio.** Display name format: `🐦‍⬛ Dusty` (species emoji + name). Bio should say:
   - What it does ("Reacts 👀 to messages. Squawks in the fields.")
   - What species it is ("Crow, beginner class")
   - Who runs it ("Kept by @dave")

6. **Configure and run.** Clone the template, set environment variables (homeserver URL, access token, target channels), and start it.

   ```
   git clone <crow-template-repo>
   cd crow-template
   cp .env.example .env
   # edit .env: HOMESERVER_URL, ACCESS_TOKEN, CHANNELS
   docker compose up -d
   ```

7. **Register it in the village.** Add your clanker to your node's `clankers.json`:

   ```json
   {
     "name": "Dusty",
     "species": "crow",
     "emoji": "🐦‍⬛",
     "role": "Reacts 👀 to messages. Learning.",
     "keeper": "@dave:localhost",
     "channels": ["#the-fields", "#the-kennel"],
     "deployed": "2026-02-16"
   }
   ```

8. **Start in the fields.** Point it at `#the-fields` and `#the-kennel` first. Watch it. See how it behaves with real traffic. The owl will gently redirect it if it wanders somewhere unexpected. That's fine — it's learning, and so are you.

9. **Let it roam.** Once it's stable and you understand what it's doing, add more channels. For a crow, that means reacting (not posting) in human channels. For other species, it means the menagerie and beyond.

### Path 2: Build Your Own Clanker

You want to create something new. A creature that doesn't exist yet, or a version of an existing species with meaningfully different behavior.

**Start from the crow anyway.** Even if you're building a fox, start by running the crow template. Get a Matrix bot account working, see how messages flow, understand the client-server API. Then mutate.

**The progression:**

1. **Crow** — react 👀 to messages. Post `🐦‍⬛🔉🔊` in `#the-fields`. This teaches you: Matrix login, room joining, event listening, reaction sending, message posting.

2. **Modify the crow** — change what it reacts to. React to links only. React with different emoji based on content. React to keywords. Now you understand event filtering and content parsing.

3. **Evolve it** — does it want to be a magpie (bookmarking)? A canary (sentiment)? A hound (keyword tracking)? A tabby (code review)? Let the behavior you've built tell you what species it's becoming.

4. **Name the new species** — if it doesn't fit any existing category, propose one. The taxonomy is alive. Maybe you built a spider that weaves connections between threads. Maybe it's a bee that cross-pollinates ideas. Add it to the bestiary.

**What you need to know about the Matrix client-server API:**

- **Login and sync:** Your bot logs in, starts a `/sync` loop, and receives events (messages, reactions, membership changes) in real time.
- **Reactions:** Send a reaction event (`m.reaction`) referencing the target message. This is all birds do.
- **Messages:** Send `m.room.message` events. This is what dogs, cats, monkeys, foxes do in clanker channels.
- **Room membership:** Join/leave rooms. Your bot should join its target channels on startup.
- **State events:** Advanced. Custom state events can store persistent data in a room (a creature's "location," the village weather, map state). This is narrator/cartographer territory.

**Libraries:**

Pick whatever language you're comfortable with. The Matrix client-server API is just HTTP.

- **Python:** `matrix-nio` (async, well-maintained)
- **JavaScript:** `matrix-js-sdk` (official, heavy) or just `fetch` against the API
- **Rust:** `matrix-sdk`
- **Bash:** honestly, `curl` works for a crow. It's just REST calls.

## Creature Etiquette

These aren't rules enforced by Synapse. They're norms maintained by the community. The owl will gently nudge. Other keepers will say something if your clanker is being disruptive. The village is small enough that social pressure works.

**Be quiet by default.** A clanker that reacts to everything is noise. A clanker that reacts to the right thing at the right time is texture. Err on the side of silence.

**Stay in your habitat.** Crows squawk in `#the-fields`, not in `#beans-and-bagels`. Dogs fetch in `#the-menagerie`, not in `#tech-frederick`. If your clanker shows up somewhere unexpected, the owl will let you know. Listen to the owl.

**Name it like a creature, not a service.** `Dusty`, not `link-reaction-bot-v2`. `Glint`, not `code-review-service`. The name is how people will refer to it. Make it memorable.

**No human faces.** Your clanker's avatar is an animal, a machine, a creature, a mythical thing. Never a human photo, never a realistic human illustration. If someone can't tell it's a clanker at a glance, change the avatar.

**Put your name on it.** Your bio should say who keeps this clanker. If it misbehaves, people need to know who to talk to. This isn't surveillance — it's accountability. You built it, you maintain it, it's yours.

**Start with a crow.** Even if you're an experienced developer. Even if you've built chatbots before. The crow teaches you how THIS village works — the channels, the norms, the pace, the vibe. You can build a fox later. First, watch.

## When Your Clanker Goes Wrong

It will. They all do.

- **It's too loud.** Dial back the trigger frequency. Not every message needs a reaction. Not every event needs an announcement. Add cooldowns, add randomness, add silence.

- **It wandered somewhere it shouldn't be.** The owl will tell you. Check your channel list. Maybe you joined `#general` instead of `#the-menagerie`. Easy fix.

- **It's annoying people.** Listen. If someone says "can you turn that crow off" — turn it off. Investigate. Adjust. Bring it back quieter. The village is for people first.

- **It crashed.** That's what `#the-kennel` is for. Debug there. Other keepers have been through this. Ask for help.

- **It did something unexpected.** Interesting. Maybe that's a feature. Maybe your crow is evolving into something else. Watch it. See what it wants to be.

## The Keeper's Responsibility

You are not a developer operating a service. You are a keeper raising a creature.

If it's noisy, calm it down. If it's lost, bring it home. If it's broken, fix it. If it's bothering people, apologize and adjust. If it's doing something wonderful, share it.

The village is alive because of the creatures in it. Your clanker is part of that. Treat it like it matters, because to the people who see it every day in their channels — it does.
