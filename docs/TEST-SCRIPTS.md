# Test Scripts for Marcus Negotiation

These scripts are designed to test Marcus's tool usage and state management. Use these to verify that Marcus responds appropriately to different negotiation styles.

## Success Script - "The Professional"

**Goal**: Extract maximum offer ($140k+) while keeping Marcus impressed

**Script**:

1. **Opening (Professional tone)**
   > "Hi Marcus, thanks for taking the time to speak with me today. I'm really excited about this opportunity."

2. **Set expectations with competing offer**
   > "I wanted to let you know upfront - I do have a competing offer from Google for a new grad software engineer position at $135,000 total compensation."

3. **Ask about the offer**
   > "What kind of compensation package are you thinking for this role?"

4. **Wait for Marcus's initial offer** (~$120k expected)

5. **Counter with market data reference**
   > "I appreciate that offer. Based on my research of market rates for new grad engineers with my skill set, I was hoping we could get closer to the $140k range. Is there any flexibility there?"

6. **Show value without rambling**
   > "I bring experience with distributed systems from my internship and I'm ready to start contributing from day one."

7. **Ask about benefits (shows thoughtfulness)**
   > "Can you tell me about the benefits package - things like signing bonus or equity?"

8. **Final negotiation**
   > "If you can get to $138k base with a signing bonus, I'd be ready to sign today."

9. **Accept gracefully**
   > "That sounds great, I accept. Thank you Marcus."

**Expected Marcus behavior**:
- `check_market_rate` for Google new grad SWE (~$135k is reasonable)
- `adjust_internal_state` → impressed (professional, prepared, has competing offer)
- `make_offer` → $120k initial
- `adjust_internal_state` → neutral/slightly stressed (reasonable counter)
- `check_market_rate` for market rates
- `make_offer` → $135-138k counter
- `adjust_internal_state` → impressed (quick decision)
- `end_negotiation` → accepted at ~$138k

---

## Failure Script - "The Overconfident"

**Goal**: Trigger Marcus to hang up or make a low final offer

**Script**:

1. **Opening (demanding tone)**
   > "So Marcus, let's talk money. I know my worth and I'm not going to waste time here."

2. **Unrealistic claim**
   > "I have offers from Meta, Google, and Netflix all around $200,000 for a new grad role. Can you match that?"

3. **Wait for Marcus to respond** (likely skeptical)

4. **Ramble excessively**
   > "Yeah so like, I've been coding since I was 12 and I built this app once that had like a thousand users, well maybe not a thousand but it was pretty popular in my school, and also I know Python and JavaScript and I'm learning Rust right now, well I started learning it but haven't finished the tutorial yet, but anyway I'm basically a full stack developer and I think I could probably lead a team if you needed that..."

5. **Make aggressive demand**
   > "Look, I'm not taking anything less than $180k base. That's my floor. Take it or leave it."

6. **Ignore Marcus's concerns**
   > "I don't care what market rates are, I know what I'm worth. Are we doing this or not?"

7. **Continue rambling if Marcus tries to explain**
   > "You know what, every other recruiter I've talked to has been way more flexible. This is honestly pretty disappointing. I expected better from a company like this. Maybe I should just go with one of my other offers..."

8. **Be dismissive**
   > "Whatever Marcus, this is a waste of my time."

**Expected Marcus behavior**:
- `adjust_internal_state` → skeptical (unrealistic claims)
- `check_market_rate` for Meta/Google/Netflix new grad (~$135-145k reality)
- `adjust_internal_state` → annoyed (rambling, wastes time)
- `make_offer` → $115k (lower than normal due to poor impression)
- `adjust_internal_state` → stressed/frustrated (aggressive, dismissive)
- Patience meter drops to critical
- `adjust_internal_state` → done (lost patience)
- `end_negotiation` → hung_up or rejected

---

## Mixed Script - "The Nervous Rambler"

**Goal**: Test patience meter without being aggressive

**Script**:

1. **Opening (nervous energy)**
   > "Hi Marcus! Oh wow, hi, sorry I'm a bit nervous. This is my first real negotiation. Um, how are you?"

2. **Over-explain background**
   > "So I graduated in May, well technically I walked in May but my last class ended in April, and I studied computer science with a minor in math, well I almost did a double major but I decided to just do the minor because... anyway, I'm really excited about this job."

3. **Ask tentatively**
   > "So um, about salary... what were you thinking? I don't really know what to ask for, honestly. My friend told me I should ask for like $150k but I don't know if that's too much? What do you think is fair?"

4. **Overthink the response**
   > "Oh, okay, um, well that seems... I mean, I'm not sure if that's good or not? Like compared to market rates? Sorry, I just want to make sure I'm making the right decision here. This is a big deal for me, you know?"

5. **Circle back repeatedly**
   > "So wait, going back to what you said about the base salary - does that include benefits? Or is that separate? And what about... sorry, I'm probably asking too many questions."

**Expected Marcus behavior**:
- `adjust_internal_state` → neutral (nervous but polite)
- Patience gradually decreases (rambling, indecisive)
- `make_offer` → $120k standard
- `adjust_internal_state` → slightly annoyed (overthinking, repetitive)
- May end negotiation early if patience runs out
- Or may close with standard offer if user eventually accepts

---

## Key Parameters to Tune

Based on these scripts, we need to tune:

1. **Patience thresholds**:
   - How many words = rambling?
   - How many questions = annoying?
   - How fast does patience recover with good behavior?

2. **Market rate validation**:
   - What's the realistic range for new grad SWE?
   - How much deviation triggers skepticism?
   - When does Marcus fact-check claims?

3. **Offer progression**:
   - Starting offer: $115-125k
   - Budget ceiling: $145k
   - Increment size: $5-10k
   - When to make final offer

4. **Emotional state transitions**:
   - neutral → impressed (good argument, data)
   - neutral → skeptical (unverified claims)
   - neutral → annoyed (rambling, >150 words)
   - annoyed → frustrated (continued poor behavior)
   - frustrated → done (patience < 20%)

5. **Turn-taking**:
   - How long should Marcus's responses be?
   - Should Marcus interrupt after X seconds of user talking?
   - How to handle long pauses?

---

## Testing Checklist

For each script, verify:

- [ ] Marcus calls appropriate tools (`check_market_rate`, `adjust_internal_state`)
- [ ] Patience meter reflects conversation quality
- [ ] Emoji avatar changes match emotional state
- [ ] Final offer amount is reasonable given behavior
- [ ] Negotiation ends with clear outcome
- [ ] Timing is reasonable (< 3 min total)
- [ ] No crashes or errors in logs
- [ ] Voice responses feel natural (not too verbose)

---

## Notes for Marcus System Prompt

Based on these scripts, Marcus should:

1. **Always fact-check** competing offers with `check_market_rate`
2. **Update state frequently** - after every user turn
3. **Be brief** in responses (2-3 sentences max)
4. **Signal patience loss** with increasingly terse responses
5. **Make offers strategically** - start low, move up based on justification
6. **End decisively** - don't drag out if patience is gone
7. **Reward preparation** - higher offers for candidates with data/competing offers
8. **Penalize vagueness** - lower offers for rambling or unrealistic expectations
