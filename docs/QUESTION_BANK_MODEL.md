# Scholarius Question Bank Model

**Status:** Architectural goal and terminology reference  
**Authority:** XML is the source of truth  
**Project maturity:** Work in progress; not production-ready

## 1. Core model

Scholarius separates the reusable question collection from the assessments
built from that collection.

```text
Question Bank
├── Questions
├── Practice Test A
├── Practice Test B
└── Practice Test C
```

A **Question Bank** owns the master question content. A bank can be used as a
pool for a random quiz, and it may also contain zero or more named **Test
Versions**.

A **Test Version** is a deliberate version or variation of an assessment made
from questions in one bank. Examples include:

- Practice Test A
- Practice Test B
- Practice Test C
- Midterm Version 1
- Midterm Version 2

Questions are referenced by stable identifiers rather than copied into each
test version. Correcting a question in the bank therefore corrects every test
version that uses it.

## 2. Why the documentation previously used “test form”

In assessment standards and testing literature, **form** often means a specific
version of a test. “Test Form A” and “Test Form B” are two versions intended to
measure the same material while using different questions or a different
ordering.

That term is technically reasonable, but it can be confused with an HTML input
form or a data-entry screen. Scholarius will therefore use **Test Version** in
its user interface and general documentation.

The implementation may still encounter terms such as `assessmentTest`,
`testForm`, or similar names when reading or exporting QTI. Those are internal
or standards-facing terms, not necessarily the labels shown to users.

## 3. XML authority

The authoritative lifecycle is:

```text
Create or import XML
        ↓
Validate and parse XML
        ↓
Register the bank
        ↓
Build or refresh the SQLite working index
        ↓
Edit through Scholarius
        ↓
Write a temporary XML file
        ↓
Validate the temporary XML
        ↓
Atomically replace the authoritative XML
```

SQLite supports filtering, searching, and editing. It is not an independent
second copy of the truth. If the XML and SQLite index disagree, the XML bank is
authoritative and the index should be rebuilt.

The initial operational layout is one authoritative bank file per bank:

```text
app/qti/<bank_identifier>.xml
```

A future standards-compatible QTI export may package shared item resources and
multiple assessment tests into a ZIP archive.

## 4. Supported question-type goal

Scholarius is intended to support five question types.

### 4.1 True/False

The learner selects exactly one of two responses.

```text
Statement: Azure Resource Groups can contain resources from multiple regions.

( ) True
( ) False
```

Initial implementation priority: **Yes**

### 4.2 Single Choice

The learner selects exactly one response from a set of choices.

```text
Which service provides ...?

( ) Choice A
( ) Choice B
( ) Choice C
( ) Choice D
```

Preferred internal name: `single-choice`  
QTI response cardinality: `single`

Initial implementation priority: **Yes**

### 4.3 Multiple Response

The learner selects two or more correct responses from a set of choices.

```text
Which TWO statements are correct?

[ ] Choice A
[ ] Choice B
[ ] Choice C
[ ] Choice D
```

Preferred user-facing name: **Multiple Response**  
Acceptable conversational name: **Multi-select**  
Preferred internal name: `multiple-response`  
QTI response cardinality: `multiple`

Initial implementation priority: **Yes**

The number of expected selections should be represented explicitly when known;
it should not be inferred only from wording such as “Select two.” The model
should be able to store:

- minimum selections;
- maximum selections;
- the complete correct-response set;
- the scoring policy.

The first implementation may use exact-match scoring: full credit only when the
selected set exactly matches the correct set. Partial-credit behavior should be
an explicit later decision.

## 5. Advanced question types requiring design work

### 5.1 Matching

A matching question associates prompts on the left with responses on the right.

```text
Azure Functions      → Serverless compute
Azure Blob Storage   → Object storage
Microsoft Entra ID   → Identity and access
```

Before implementation, the project should decide:

- whether right-side answers may be reused;
- whether distractor answers are allowed;
- whether every left-side item must be matched;
- how duplicate visible labels are distinguished internally;
- whether answer order is randomized;
- exact-match versus per-pair scoring;
- how the editor represents pairs;
- how the learner answers without requiring drag-and-drop.

The XML should store stable identifiers for both sides and an explicit mapping,
not merely two parallel text arrays.

Conceptual model:

```xml
<matchingInteraction>
  <left identifier="L1">Azure Functions</left>
  <right identifier="R1">Serverless compute</right>
  <match left="L1" right="R1"/>
</matchingInteraction>
```

The final XML must use the selected Scholarius/QTI representation rather than
assuming this conceptual example is the finished schema.

### 5.2 Ordering

An ordering question asks the learner to arrange items into the correct
sequence.

```text
1. Create the resource group
2. Create the virtual network
3. Create the virtual machine
```

Before implementation, the project should decide:

- whether all items must be used;
- whether some items are distractors;
- whether ties or equivalent orders are allowed;
- exact-order versus partial-credit scoring;
- how the initial randomized order is generated;
- how the editor stores and changes the canonical order;
- how keyboard and screen-reader users move items without drag-and-drop.

The XML should store each item with a stable identifier and store the correct
sequence as an ordered list of those identifiers.

Conceptual model:

```xml
<orderingInteraction>
  <item identifier="S1">Create the resource group</item>
  <item identifier="S2">Create the virtual network</item>
  <item identifier="S3">Create the virtual machine</item>
  <correctOrder>S1 S2 S3</correctOrder>
</orderingInteraction>
```

Again, this illustrates the data requirement; it is not yet a final schema.

## 6. Test Versions

A bank may contain several named test versions. A test version references bank
questions and can define presentation settings.

Minimum planned properties:

```text
identifier
bank identifier
title
description
ordered question references
shuffle questions
```

Possible later properties:

```text
time limit
passing score
question points
section definitions
domain composition
random-selection rules
attempt limits
feedback policy
```

The first implementation should support **fixed Test Versions**: the author
chooses the exact questions and their order. Rule-based versions, such as “draw
50 questions with these domain percentages,” can be added later without
changing the distinction between a bank and a test version.

## 7. Terminology table

| Scholarius term | Meaning |
|---|---|
| Question Bank | Master collection of reusable questions |
| Test Version | A named assessment variation referencing questions in one bank |
| Random Quiz | A runtime selection drawn from the bank rather than a fixed version |
| Single Choice | Exactly one correct selection from several choices |
| Multiple Response | Two or more correct selections from several choices |
| Matching | Associate left-side prompts with right-side responses |
| Ordering | Arrange items into a correct sequence |
| Working Index | SQLite representation used to search and edit authoritative XML |

## 8. Initial implementation boundary

The near-term implementation should concentrate on a complete vertical path for:

- True/False;
- Single Choice;
- Multiple Response;
- XML import and validation;
- editing and safe XML rewrite;
- fixed Test Versions referencing questions in the same bank.

Matching and Ordering should remain visible roadmap goals, but should not be
represented as complete merely because their names can be stored in a database.
Their interaction model and scoring rules require a deliberate design pass.

## Management workflow implemented

The first management workflow is now organized around a bank-level landing card:

1. **Bank Details** — title, description, author, and version.
2. **Test Settings** — default test name and description, optional time limit, default question count, passing percentage, shuffle behavior, review, and explanation visibility.
3. **Questions** — the existing XML-backed question editor.
4. **Test Versions** — planned named versions such as Practice Test A, B, and C.
5. **Domains & Subjects** — planned hierarchy for broad domains and narrower subject areas.

The Create Question Bank wizard collects identity, descriptive metadata, and default test settings. Completion creates and validates the authoritative XML file, registers it with Scholarius, and builds the replaceable SQLite editing index.
