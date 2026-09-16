# Launch Content — ClearGlass v2.1.1

Ready-to-post copy. Nothing here is auto-published; review, then post from your
own accounts.

---

## LinkedIn — primary post

> **Most "AI automation" is a chatbot with extra steps. Real automation makes a decision and then *acts* — and can prove why.**
>
> This week I shipped a workflow engine with one rule: advance exactly **one** keystone outcome per day, and gate everything else behind it. No 14-item backlog cosplaying as a strategy. One outcome → it unlocks the rest.
>
> I paired it with a forensic pipeline that, in a live run, flagged a billing collision, an insider snoop (3σ over baseline), and unencrypted PHI — in milliseconds, each traceable back to the exact event that triggered it.
>
> The lesson from building it: agents don't need to be smarter. They need to be **decisive and auditable.** Constraint is the feature.
>
> It's live on npm today: `npm i @clearglassinc/opal-koboi`
>
> What's the one outcome your systems should be defending today? 👇
>
> #AIAutomation #AgenticAI #Cybersecurity #BuildInPublic

---

## Follow-up thread (post 1–2 days later, as replies or a new post)

**1/** People keep asking how the "one outcome a day" engine actually enforces focus. It's a dependency gate: the keystone (your single P0) is the only thing startable. Everything else is `LOCKED` until the keystone lands *with evidence*. Try to start another track early → refused.

**2/** Why evidence? Because "done" with no proof is how teams lie to themselves. Completing the keystone requires a success-metric artifact; only then does the gate reconcile and unlock the rest of the day. The system literally won't let you skip ahead.

**3/** The audit side is the part regulated teams care about. Every accepted alert is sealed into a hash-chained ledger + clustered into an incident. Any score reconstructs back to the facts that produced it. "We think it's fine" → "here's the chain."

**4/** All of it runs on the standard library — no heavyweight runtime to babysit. Web/API/UI are optional seams. 90 automated tests, green. Open core (MIT) on npm; hosted + enterprise tiers for teams that need SSO, on-prem, and retention SLAs.

**5/** If you run autonomous agents and your oversight story is "we read the logs sometimes," let's talk. Building 3 design-partner integrations in exchange for case studies. DM me.

---

## X / short form

> Shipped an AI automation engine with one rule: one keystone outcome a day, everything else gated behind it. Plus a forensic pipeline that caught fraud + an insider snoop + unencrypted PHI in a live run — all auditable to the source event.
>
> Constraint is the feature. `npm i @clearglassinc/opal-koboi`
