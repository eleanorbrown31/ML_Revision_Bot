# Systems thinking, complexity, and management frameworks — Revision sheet

---

## 1. Goldratt's Theory of Constraints (TOC)

**Origin:** Eliyahu Goldratt, Israeli physicist and business consultant. Introduced in his 1984 novel *The Goal*.

**Central claim:** Every system has at least one constraint limiting its performance. Improving anything else is wasted effort until you deal with that constraint.

**The chain metaphor:** The strength of a chain is determined by its weakest link. Strengthening any other link changes nothing.

### The five focusing steps

1. **Identify** the constraint — find the bottleneck
2. **Exploit** the constraint — get maximum output from it without major investment
3. **Subordinate** everything else — align all other processes to support the constraint, not to maximise their own output
4. **Elevate** the constraint — invest in expanding its capacity if needed
5. **Repeat** — once broken, a new constraint will appear elsewhere

Step 3 is the one that surprises people. Optimising non-constraints can harm the system by overloading the bottleneck or building inventory in front of it.

### Throughput accounting

Goldratt rejected traditional cost accounting as misleading for operational decisions. TOC measures performance through:

- **Throughput** — the rate at which the system generates money through sales
- **Inventory** — money tied up in the system
- **Operating expense** — money spent converting inventory into throughput

The goal is to increase throughput while reducing inventory and operating expense, not to optimise local efficiencies in isolation.

### Applications

TOC originated in manufacturing but has been applied to project management (*Critical Chain*, 1997), software development (influenced Lean and Kanban), healthcare, logistics, and knowledge work generally.

---

## 2. Criticisms of TOC

**Assumes a single constraint.** Real systems often have multiple interacting constraints. Fixing one bottleneck can expose several others simultaneously, or constraints can shift faster than the five-step cycle can respond.

**It is mechanistic.** TOC treats organisations like linear chains. Human organisations are webs: their constraints are often invisible, contested, or unstable.

**Neglects strategic direction.** By focusing tightly on throughput, TOC can optimise a system that is heading in the wrong direction.

**Throughput accounting is contested.** It de-emphasises cost control in ways that do not integrate easily with standard reporting frameworks.

**Can create local complacency.** "Subordinate everything else to the constraint" discourages improvement elsewhere, even where modest gains would compound over time.

**The complexity critique (the sharpest one):** In a complex adaptive system, the "chain" is itself emergent and shifting. Fixing today's constraint may restructure the system in ways that create new constraints in unexpected places. Optimising for throughput can also reduce adaptive capacity, making the system efficient but brittle. This is a known failure mode in ecological systems and has clear organisational analogues.

---

## 3. Contrasting frameworks — brief orientations

| Framework | Core focus | Relation to TOC |
|---|---|---|
| **Lean / Toyota Production System** | Eliminate waste across the whole value stream | Shares hostility to local optimisation but distributes improvement responsibility rather than concentrating on one constraint |
| **Six Sigma** | Reduce variation and defects through statistical methods | Where TOC asks "where's the bottleneck?", Six Sigma asks "where's the variability?" Not incompatible, but different root assumptions |

---

## 4. Cynefin framework

**Origin:** Dave Snowden, developed at IBM in the late 1990s, built directly from complexity theory and complex adaptive systems research. The name is Welsh, meaning roughly "habitat" or "the place of your multiple belongings." Pronounced *kuh-NEV-in*.

**What it is:** A sense-making framework, not a process model. It helps you understand what kind of situation you are in before deciding how to act. Most management frameworks skip this step entirely.

### The five domains

**Clear** (formerly Simple)
Cause and effect are obvious and repeatable. Best practice exists. Sense, categorise, respond. Standard expense processing, for example.

**Complicated**
Cause and effect exist but require analysis or expertise to see. Good practice exists in the plural. Sense, analyse, respond. This is where TOC, Six Sigma, and most management consulting frameworks live. Expert knowledge is genuinely valuable here.

**Complex**
Cause and effect can only be understood in retrospect. No single right answer; practice emerges from experimentation. Probe, sense, respond. Most organisational change, culture, and learning transformation sits here. Best practice imported from elsewhere is a trap.

**Chaotic**
No discernible cause and effect. Act first to stabilise, then sense, then respond. Crisis management territory.

**Confused / disorder** (the centre)
You do not know which domain you are in. The most dangerous state, because people default to their preferred domain regardless of what the situation actually requires.

### Key insights for EPA

The cliff edge between Clear and Chaotic matters: stable, well-understood systems can tip suddenly into chaos if over-managed or if core assumptions break.

Applying Complicated-domain tools (analysis, best practice, TOC) to Complex problems is a category error. Snowden is pointed about this. In Complex situations you run safe-to-fail experiments; you do not impose solutions.

---

## 5. Soft Systems Methodology (SSM)

**Origin:** Peter Checkland, Lancaster University, 1970s onwards. Built as a direct response to the failure of hard systems engineering when applied to messy human problems.

### The starting insight

Hard systems thinking assumes the system and its goal are given; you just need to optimise it. SSM begins from the observation that in human situations, people disagree about what the system is, what it is for, and what counts as improvement. The problem is not just complicated. It is *contested*.

Checkland called these "soft" problems or "messes," borrowing the term from Russell Ackoff (another systems thinker worth knowing in his own right).

### CATWOE

The core analytical tool. Used to construct **root definitions** — explicit statements of what a system is doing and the worldview that makes that meaningful.

| Letter | Stands for | What it asks |
|---|---|---|
| **C** | Customers | Who benefits or suffers? |
| **A** | Actors | Who carries out the activities? |
| **T** | Transformation | What is being changed or converted? |
| **W** | Weltanschauung | What worldview makes this transformation meaningful? |
| **O** | Owner | Who could stop this system? |
| **E** | Environment | What constraints are taken as given? |

The *Weltanschauung* is the most important element. It makes explicit that every system description embeds assumptions and values. There is no view from nowhere. Different stakeholders will produce different CATWOE analyses of the same situation, and that divergence is the point.

### The SSM cycle

1. Enter the problem situation without immediately trying to solve it
2. Build **rich pictures** — literal drawings mapping relationships, tensions, structures, and concerns. Non-linear by design.
3. Construct root definitions using CATWOE
4. Build **conceptual models**: idealised logical models of what the system *would* do, not descriptions of reality
5. Compare conceptual models with the actual situation; identify gaps
6. Identify changes that are both *systemically desirable* and *culturally feasible*
7. Take action; then cycle back

### Connection to critical systems thinking

SSM feeds into a broader tradition of critical systems thinking (Ulrich, Jackson) which asks not just "is the system working?" but "working for whom?" This is a political question that most management frameworks sidestep.

---

## 6. Ashby's Law of Requisite Variety

**Origin:** W. Ross Ashby, British psychiatrist and cybernetician. Published in *An Introduction to Cybernetics* (1956). Ashby was working before complexity theory had crystallised, but he was intuiting the same territory.

**The law:** Only variety can absorb variety. More formally: the number of possible states a controller can produce must be at least as great as the number of disturbances it needs to handle. If the environment generates more variety than the regulator can respond to, the system will be overwhelmed.

### A concrete illustration

A thermostat has very limited variety: on or off. Sufficient for a simple room, because the disturbances are also limited. Using the same thermostat to regulate the climate of a rainforest fails because the environment has vastly more variety than the controller.

### Two responses to a variety gap

When the environment has more variety than the regulator:

1. **Increase regulator variety** — more capability, flexibility, autonomy in the responding system
2. **Reduce environmental variety** — standardisation, simplification, imposed constraints

Most management instinctively reaches for the second. In genuinely complex environments, this eventually fails: you cannot standardise away real complexity; you hide it until it erupts elsewhere.

### Implications for L&D

Training that teaches fixed procedures *reduces* learner variety. This works until the environment produces something the procedure does not cover. Building adaptive capacity — requisite variety in the learner — is a fundamentally different design goal and requires a different kind of curriculum.

**EPA connection:** A TNA system that captures the full diversity of roles, competencies, and learning contexts is itself an attempt to build requisite variety into the analysis process. A simpler system with fewer nodes and relationships will be overwhelmed by organisational complexity it cannot represent.

---

## 7. Rittel's wicked problems

**Origin:** Horst Rittel (German design theorist, UC Berkeley) and Melvin Webber. *Dilemmas in a General Theory of Planning* (1973). Written in direct response to the failures of 1960s urban planning.

### Tame vs wicked

**Tame problems** are well-defined, have a clear stopping point, and have objectively correct solutions. Chess, engineering calculations, logistics optimisation. Hard, but solvable.

**Wicked problems** resist this treatment entirely. The problem itself is contested, solutions generate new problems, there is no definitive test for success, and every intervention changes the situation you are trying to address.

### Key properties of wicked problems

1. **No definitive formulation.** You cannot fully understand the problem without attempting a solution.
2. **No stopping rule.** You never *solve* a wicked problem, only resolve it better or worse.
3. **Solutions are good or bad, not true or false.** Judged by stakeholders with different values, not by an objective measure.
4. **No immediate test.** Consequences unfold over time and may be irreversible.
5. **One-shot operation.** Unlike scientific experiments, you cannot trial-and-error without real consequences.
6. **Every wicked problem is unique.** Solutions do not transfer cleanly from one context to another.
7. **Every wicked problem is a symptom of another problem.** There is no root cause, only levels of description.

### The political point

Rittel was making a pointed argument: applying scientific problem-solving to inherently social problems is a category error. The planning disasters of the 1960s followed from treating wicked problems as tame ones. The same error recurs in skills strategy, technology transformation, and organisational change whenever leaders reach for a "solution."

### Connection to complexity theory

Wicked problems are wicked precisely *because* they are embedded in complex adaptive systems. The system keeps adapting in response to every intervention. Complexity theory provides the mechanism underneath Rittel's phenomenology.

---

## 8. Complexity theory and Complex Adaptive Systems

**Origin:** Santa Fe Institute, 1980s and 1990s. Brought together physicists, biologists, economists, and computer scientists around the observation that many systems generate behaviours that cannot be predicted or explained by analysing their parts in isolation.

### Core concepts

**Complex Adaptive Systems (CAS)**
Systems composed of many agents that interact, adapt, and co-evolve. Each agent follows local rules, but system-level behaviour *emerges*; it is not designed or controlled centrally. Examples: ant colonies, immune systems, financial markets, organisations, ecosystems, languages.

**Emergence**
Properties that arise at the system level but do not exist at the component level. Consciousness from neurons. Market prices from individual transactions. Culture from individual behaviours. Emergence cannot be engineered directly; you can only create conditions that make it more or less likely.

**Non-linearity**
Small causes can have large effects; large interventions can have negligible ones. This is why effort and outcome are not proportional in complex systems, and why management intuitions built on linear thinking repeatedly fail.

**Sensitive dependence on initial conditions**
Tiny differences in starting conditions produce radically different trajectories over time. Long-range prediction in complex systems is structurally impossible, not just technically difficult.

**Fitness landscapes**
A metaphor from evolutionary biology. Agents navigate a landscape of possible states, searching for peaks. But the landscape shifts as other agents adapt. There is no final optimal solution, only ongoing adaptation.

**Edge of chaos**
Complex systems are most adaptive and generative when poised between rigid order and complete disorder. Too much order and the system cannot adapt; too much chaos and it cannot function. This has direct implications for organisational design and learning culture: highly standardised training keeps organisations in the ordered domain, efficient but brittle.

### The paradigm shift

Complexity theory represents a genuine break with Newtonian management thinking. Classical management inherited a Newtonian worldview: systems are predictable, controllable, and decomposable. Understand the parts, engineer the whole.

Complexity theory shows this works for a narrow class of problems and fails for most of the interesting ones. The connection to post-structuralist critiques of Enlightenment rationalism is not superficial: both insist that systems are irreducibly entangled, meaning is emergent, and the observer changes the observed. Foucault's account of power as distributed through systems, producing effects nobody designed, sits closer to complexity theory than to any classical management framework.

---

## 9. How the frameworks connect

| Framework | Core question | Best domain fit | Relation to complexity theory |
|---|---|---|---|
| **TOC** (Goldratt) | Where is the bottleneck? | Complicated | Assumes linear chains; breaks down in CAS |
| **Lean** | Where is the waste? | Complicated | More distributed than TOC; still assumes legible systems |
| **Six Sigma** | Where is the variability? | Complicated | Assumes measurable, stable processes |
| **Cynefin** (Snowden) | What kind of situation is this? | All domains (meta) | Built directly on CAS research |
| **SSM** (Checkland) | What is the system for, and for whom? | Complex, wicked | Constructivist; compatible with CAS thinking |
| **Requisite Variety** (Ashby) | Does the controller match the environment's complexity? | Complex | Anticipates CAS; the cybernetic foundation |
| **Wicked Problems** (Rittel) | Is this problem socially contested and open-ended? | Complex, chaotic | CAS explains the mechanism behind wickedness |
| **CAS / Complexity theory** | How do system-level properties emerge from local interactions? | Complex | The underlying science |

### The synthesis argument

These frameworks form a coherent critique of mechanistic management thinking:

- **Ashby** explains *why* simple controllers fail in complex environments — insufficient variety
- **Rittel** explains *why* standard problem-solving fails on social challenges — the problems are structurally different
- **Cynefin** provides a diagnostic map for *which kind of situation you are in*
- **SSM** provides a methodology for *working with wicked problems in practice*
- **Complexity theory** is the scientific foundation for all of the above

TOC works well in the Complicated domain and fails in the Complex one. Knowing which domain you are in is the real skill, and it is the one most frameworks do not address.

---

## 10. EPA framing cheat sheet

**If a scenario applies a technical framework to a human or social problem:**
Argue using Cynefin that the problem sits in the Complex domain, where probe-sense-respond beats analyse-then-act. Name Rittel's wicked problem properties if the problem is contestable and open-ended. A strong answer names *why* the framework being used is the wrong category of tool, not just that it is incomplete.

**If a scenario's solution fails to adapt or scale:**
Invoke Ashby's Law. The regulator lacks sufficient variety to match the environment's complexity. Name both responses to the variety gap (increase regulator variety vs reduce environmental variety) and argue which is appropriate for the scenario.

**If a scenario involves stakeholder disagreement about what the system should do:**
SSM is the right tool. CATWOE makes conflicting Weltanschauungen explicit. Rich pictures map the mess before any solution is proposed. Note that the disagreement is not a dysfunction to be resolved; it is diagnostic information about the nature of the problem.

**If a scenario optimises one thing at the expense of system resilience:**
Use the edge-of-chaos argument. Efficient systems are often brittle systems. Name the tension between throughput optimisation (TOC logic) and adaptive capacity (complexity logic).

**If a scenario presents fairness or governance as a purely technical problem:**
Connect to the Kleinberg/Chouldechova argument from the Fairness in ML revision notes. Choosing a fairness metric is itself a values decision, which makes it a wicked problem: different stakeholders will assess solutions as good or bad rather than true or false, and there is no objective stopping rule.

**For the TNA project specifically:**
A GraphRAG system mapping skills and learning needs across an organisation is an attempt to model a complex adaptive system. The graph structure is more appropriate than a relational model precisely because it can represent emergent, non-linear relationships between competencies, roles, and contexts. Framing this explicitly in the EPA professional discussion, using Ashby's Law and CAS concepts, gives the architectural choice theoretical grounding that goes beyond the technical.

**General move (consistent with the methodology sheet):** Name the framework, name its underlying assumption, name where that assumption breaks, name what fills the gap. This demonstrates critical evaluation rather than rote recall — which is the KSB being tested.
