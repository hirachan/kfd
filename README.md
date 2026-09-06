# Knowledge-First Development (KFD)

[日本語](README_ja.md)

KFD is a development workflow for software built and maintained with AI coding agents.

Its central idea is simple:

> **Keep product meaning in Knowledge, not in implementation code.**

```text
Human intent
    ↓
Knowledge        Why / What
    ↓
Tests            Evidence
    ↓
Implementation   How
```

KFD does not try to make AI write code the same way humans always have. It starts from the assumption that AI changes the role source code plays in software development.

## Why KFD exists

A natural first approach to AI-assisted development is to make the agent follow a clean architecture very strictly: layers, boundaries, abstractions, naming rules, and so on.

That can work at first. But as changes accumulate, another problem appears: even a small product change may require the agent to read and reason about a large amount of unrelated code before it can safely modify anything.

This is one form of technical debt: past implementation choices increase the cost of future changes. With AI agents, that cost is paid not only in engineering time, but also in context, tokens, and repeated rediscovery.

That led to a more fundamental question:

> If I ask AI to writes the code, does source code still need to be the place where humans understand the product?

One extreme answer would be to remove programming languages entirely and generate executable binaries directly from natural language.

In practice, that throws away an enormous ecosystem. Programming languages have compilers, libraries, frameworks, tools, tests, examples, documentation, and decades of accumulated knowledge. AI models also have far more useful experience with programming languages than with direct natural-language-to-binary generation.

KFD therefore takes a different position:

> **Programming code is still extremely useful, but it can be treated primarily as an implementation medium rather than the primary specification of the product.**

Humans should review the meaning of the product at a higher level. AI can then use ordinary programming languages as a practical intermediate representation for producing the running system.

## Knowledge is the source of truth

In KFD, each independently changeable area of product meaning is represented as a **Knowledge Unit**.

For each unit:

- `knowledge.yaml` describes the current **Why** and **What**;
- tests provide **Evidence** that the implementation conforms to that Knowledge;
- source code is the **How**;
- `decisions.yaml` optionally preserves important past decisions that would otherwise be rediscovered incorrectly.

The implementation is still important. It just no longer has to carry the full burden of explaining the product to humans and AI at the same time.

This changes the direction of development from:

```text
Prompt -> Code -> infer what the product now means
```

to:

```text
Prompt -> Knowledge -> Tests -> Implementation
```

## Not a big-upfront-specification method

KFD does **not** require describing the entire application before useful work can begin.

For each request, the agent identifies the smallest coherent slice that is actually being changed now.

```text
Prompt
  |-- current implementation slice -> Knowledge -> Tests -> Implementation
  `-- valuable remaining intent ----> Parking Lot
```

Only the current slice is refined into Knowledge. Ideas and observations worth keeping, but not part of the current work, stay coarse in `parking-lot.md`.

This is important for both humans and AI: the Knowledge Base should contain current product meaning, not an ever-growing collection of speculative future requirements.

## Small context is a feature

A KFD Knowledge Unit is intended to be understandable and changeable without reading the whole repository.

The agent starts with the smallest useful context:

1. project instructions;
2. the Knowledge index;
3. the target Knowledge Unit;
4. directly affected tests;
5. the mapped implementation.

It expands outward only when evidence shows that more context is required.

The goal is not merely cleaner documentation. The goal is to reduce rediscovery and keep routine changes local enough that AI agents can work safely without repeatedly loading the entire system into context.

## Human decisions stay human

KFD deliberately separates implementation decisions from product decisions.

If two reasonable interpretations would produce different product behavior, the agent stops with **Decision Required** rather than silently choosing one.

When product meaning changes, the agent updates Knowledge first and presents a **Knowledge Review** before implementation.

This gives humans a compact review surface for questions such as:

- What will users be able to do?
- What will the system store or expose?
- What business rule is changing?
- What happens to existing data?
- What will the system explicitly not do?

The human reviews product meaning. The agent can handle much more of the implementation detail.

## Existing projects can adopt KFD gradually

KFD is not only for new projects.

There is no migration that requires reverse-engineering an existing application into a complete Knowledge Base.

When KFD is introduced to an existing repository, the agent preserves the existing framework, source layout, and test layout. When a product area is changed for the first time, it captures only the minimum current meaning needed to make that change safely.

```text
Existing application
        ↓
change one product area
        ↓
capture its current meaning
        ↓
Knowledge
        ↓
Tests
        ↓
Implementation change
```

If existing behavior is ambiguous — for example, it may be an accidental implementation detail rather than intended product behavior — KFD does not automatically turn it into a requirement. The agent asks.

Over time, Knowledge grows where the product actually changes.

## What KFD does not mean

KFD does not mean that source code quality no longer matters. Poorly coupled implementation can still make changes expensive, and KFD can expose that problem when one Knowledge Unit repeatedly requires unrelated code to be read.

KFD also does not mean that every implementation detail belongs in Knowledge. Knowledge should describe stable product meaning. Implementation details remain in the implementation unless they materially affect externally observable behavior, persistence, permissions, security, compatibility, or other product semantics.

And KFD is not a second change log. Git remains the ordinary history.

## Core files in a KFD project

A project using KFD normally contains:

```text
project-root/
  AGENTS.md
  parking-lot.md
  checkpoint.yaml          # optional
  knowledge/
    index.yaml
    <knowledge-id>/
      knowledge.yaml
      decisions.yaml       # optional
  <existing source and test layout>
  userstories.md           # generated view; optional
```

The shared Skill contains the KFD method. The repository contains that product's Knowledge.

Existing projects do not need to reorganize their application into a KFD-specific source tree.


## Generating a human-readable view

Knowledge is deliberately split into small Knowledge Units so that AI can work with a small amount of context. That structure is useful for development, but it is not always the easiest format for a human who wants to understand the product as a whole.

For that purpose, KFD can generate an integrated human-readable view such as `userstories.md`.

```text
knowledge/
  account/knowledge.yaml
  order/knowledge.yaml
  payment/knowledge.yaml
          ↓
      generate
          ↓
    userstories.md
```

`userstories.md` is **generated from the current Knowledge Base**. It may reorganize multiple Knowledge Units around actors, user goals, flows, rules, and visible behavior so that the product is easier to read as one coherent specification.

For example:

```text
Generate userstories.md from the current Knowledge Base.
```

or:

```text
Generate a complete human-readable specification from KFD Knowledge.
```

The agent reads all relevant Knowledge Units and produces the integrated view in the project's human-facing language.

A generated view must:

- preserve the meaning already present in Knowledge;
- combine related information across Knowledge Units when that improves readability;
- omit implementation details unless the requested view needs them;
- never invent rules, states, permissions, guarantees, or behavior;
- clearly state that the file is generated.

`userstories.md` is **not another source of truth**.

```text
Human edits to product meaning
            ↓
      knowledge.yaml
            ↓
          generate
            ↓
       userstories.md
```

If a human wants to change product behavior, the change belongs in the relevant `knowledge.yaml`, not directly in `userstories.md`.

Generating this view is optional and is not required for normal KFD development. It is useful when someone wants to review the whole product, share a readable specification, onboard another person, or inspect how several Knowledge Units fit together.

Once `userstories.md` exists, product-meaning changes that affect it should refresh the generated view so that it does not drift away from the Knowledge Base.

## Using the Skill

This repository is an Agent Skill. `SKILL.md` is the entry point, with supporting references, templates, and examples loaded only when useful.

Install the Skill using the mechanism provided by your Agent Skills-compatible tool, then open a new or existing project and say, for example:

```text
Use KFD for this project.
```

There is no initialization script and no separate migration command.

On first use, the agent adds only the KFD files that are actually needed, preserves existing project instructions, and asks for the human-facing project language if it has not already been established.

To make KFD usage visible to everyone who clones the repository, commit a small KFD declaration in `AGENTS.md` together with the project's Knowledge files.

## Skill repository structure

```text
SKILL.md            KFD workflow and agent instructions
references/         detailed material loaded when needed
assets/             templates used when creating KFD files
examples/           worked examples for reference
README.md           this document
README_ja.md        Japanese version
CHANGELOG.md        version history
```

Examples are learning aids, not product Knowledge and not mandatory context for normal work.

## The short version

KFD is based on three separations:

```text
Knowledge       = Why / What
Tests           = Evidence
Implementation  = How
```

The purpose is not to write more documentation.

The purpose is to give humans a compact, reviewable representation of product meaning, while letting AI use the enormous existing programming ecosystem to produce and change the implementation with as little unrelated context as possible.

That is the core idea of **Knowledge-First Development**.
