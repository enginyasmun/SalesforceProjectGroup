"""Eight-week Salesforce graduate development curriculum.

The learning loop used throughout the portal is:
Learn -> Build -> Prove -> Explain -> Defend -> Improve.
"""

RUBRIC = [
    {"key": "business", "label": "Business understanding", "max_score": 20, "description": "Explains users, problem, scope, rules, and business value."},
    {"key": "evidence", "label": "Evidence and completeness", "max_score": 20, "description": "Provides clear artifacts, tests, examples, and complete deliverables."},
    {"key": "salesforce", "label": "Salesforce reasoning", "max_score": 20, "description": "Uses appropriate Salesforce design choices and explains tradeoffs."},
    {"key": "communication", "label": "Communication and defense", "max_score": 20, "description": "Explains the work clearly and answers technical follow-up questions."},
    {"key": "professionalism", "label": "Professional quality", "max_score": 20, "description": "Organizes work, responds to feedback, and accurately identifies ownership."},
]


def step(title, actions, output):
    return {"title": title, "actions": actions, "output": output}


CURRICULUM = [
    {
        "number": 1,
        "phase": "Understand",
        "title": "Know the project before you explain it",
        "focus": "Build a truthful project baseline and identify exactly what you completed.",
        "estimated_time": "4 to 6 hours",
        "interview": "Tell me about the Salesforce project you worked on.",
        "competencies": ["Project discovery", "Ownership", "Evidence management", "Project storytelling"],
        "steps": [
            step("Learn", ["Read the project brief from beginning to end.", "Identify the business problem, users, scope, and expected outcomes."], "A one-paragraph project baseline."),
            step("Build", ["Create a personal work plan for the assigned project step.", "Separate your work from work completed by teammates."], "An ownership checklist."),
            step("Prove", ["Collect screenshots, diagrams, links, test results, and notes.", "Label each artifact with the requirement it proves."], "An evidence inventory."),
            step("Explain", ["Use business problem, users, role, solution, result, and lesson.", "Record a 60-second project introduction."], "A concise project introduction."),
            step("Defend", ["Answer why the project exists, who uses it, and what you personally did.", "Remove any statement you cannot support with evidence."], "Defensible project claims."),
            step("Improve", ["Review the recording for clarity and specificity.", "Rewrite vague or exaggerated statements."], "A stronger final introduction."),
        ],
        "knowledge_check": [
            "What is the business problem in one sentence?",
            "Who are the main users and what outcome does each need?",
            "Which artifacts prove your personal contribution?",
        ],
        "defense_questions": [
            "What did you personally build or configure?",
            "What was completed by someone else?",
            "What would you verify before presenting this as production-ready?",
        ],
        "presentation_topic": "Introduce the project and your real contribution",
        "presentation_slides": ["Business problem", "Users and process", "My contribution", "Evidence", "Lessons and improvements"],
    },
    {
        "number": 2,
        "phase": "Requirements",
        "title": "Turn the project brief into testable requirements",
        "focus": "Understand stakeholders, process, scope, business rules, exceptions, and acceptance criteria.",
        "estimated_time": "5 to 7 hours",
        "interview": "How do you gather and clarify requirements?",
        "competencies": ["Discovery", "User stories", "Acceptance criteria", "Traceability"],
        "steps": [
            step("Learn", ["Identify stakeholders and their goals.", "Review the process from request to outcome."], "A stakeholder and process map."),
            step("Build", ["Write at least five user stories.", "Add constraints, exceptions, and security needs."], "A prioritized story set."),
            step("Prove", ["Write Given/When/Then acceptance criteria.", "Trace each criterion to a project deliverable."], "A requirements traceability table."),
            step("Explain", ["Describe how you turn a vague request into testable scope."], "A two-minute requirements explanation."),
            step("Defend", ["Explain assumptions and unresolved questions.", "Show how a tester determines pass or fail."], "A defensible requirements package."),
            step("Improve", ["Remove solution language from business requirements.", "Add missed negative and permission scenarios."], "Refined requirements."),
        ],
        "knowledge_check": ["How is a requirement different from a solution?", "What makes acceptance criteria testable?", "Which nonfunctional requirements matter here?"],
        "defense_questions": ["What question changed your understanding of the request?", "How did you handle conflicting stakeholder needs?", "What is explicitly out of scope?"],
        "presentation_topic": "Requirements, stakeholders, user stories, and acceptance criteria",
        "presentation_slides": ["Business request", "Stakeholders", "Process and rules", "User stories", "Acceptance criteria and open questions"],
    },
    {
        "number": 3,
        "phase": "Foundation",
        "title": "Design data, access, quality, and reporting",
        "focus": "Connect the object model, security model, validation, duplicate management, reports, and dashboards.",
        "estimated_time": "5 to 7 hours",
        "interview": "How did you design the data model and security?",
        "competencies": ["Data modeling", "Sharing and visibility", "Data quality", "Analytics"],
        "steps": [
            step("Learn", ["Review relationship types and access layers.", "Identify reporting questions the business needs answered."], "A design-notes sheet."),
            step("Build", ["Create the core objects, fields, relationships, and security configuration.", "Create validation and duplicate rules."], "A working declarative foundation."),
            step("Prove", ["Create an ERD and security matrix.", "Test access as different users and capture evidence."], "Architecture and access evidence."),
            step("Explain", ["Explain every relationship and access decision.", "Connect reports to business decisions."], "A data-and-security walkthrough."),
            step("Defend", ["Separate object, field, record, and sharing access.", "Explain why each relationship is lookup or master-detail."], "Defensible design decisions."),
            step("Improve", ["Review for over-permissioning and unnecessary fields.", "Improve labels, descriptions, help text, and report usability."], "A cleaner foundation."),
        ],
        "knowledge_check": ["What is the difference between object access and record access?", "When should master-detail be avoided?", "How do validation and duplicate rules solve different problems?"],
        "defense_questions": ["Why did you choose this relationship type?", "How does an external user obtain record access?", "What changes when data volume grows?"],
        "presentation_topic": "Data model, security, data quality, reports, and dashboards",
        "presentation_slides": ["Object model", "Relationship decisions", "Security model", "Quality controls", "Reports and business value"],
    },
    {
        "number": 4,
        "phase": "Development",
        "title": "Build bulk-safe Apex and meaningful tests",
        "focus": "Use triggers, services, batch processing, scheduling, error handling, and tests to demonstrate developer reasoning.",
        "estimated_time": "6 to 9 hours",
        "interview": "Describe an Apex solution you built and how you tested it.",
        "competencies": ["Apex design", "Bulkification", "Testing", "Asynchronous Apex"],
        "steps": [
            step("Learn", ["Review trigger contexts, governor limits, and test isolation.", "Identify the transaction boundaries and failure modes."], "A technical design outline."),
            step("Build", ["Implement trigger-handler separation and reusable services.", "Implement batch and schedulable behavior where required."], "Working Apex components."),
            step("Prove", ["Test positive, negative, bulk, and update paths.", "Use meaningful assertions and realistic volume."], "A test matrix and results."),
            step("Explain", ["Walk through collections, queries, DML, and error handling.", "Explain why tests prove behavior rather than only coverage."], "A code-design walkthrough."),
            step("Defend", ["Explain behavior for 200 records and partial failures.", "Discuss sharing, CRUD/FLS, and user-mode operations."], "A technical defense."),
            step("Improve", ["Review for SOQL/DML in loops, recursion, and weak assertions.", "Refactor duplicated or tightly coupled logic."], "Maintainable Apex."),
        ],
        "knowledge_check": ["Why must trigger logic be bulk-safe?", "What should a negative test assert?", "When is Batch Apex appropriate?"],
        "defense_questions": ["How does the code behave with 200 records?", "What happens when one record fails?", "How is security enforced?"],
        "presentation_topic": "Apex design, bulkification, error handling, batch Apex, and testing",
        "presentation_slides": ["Technical requirement", "Trigger and service design", "Bulk and error strategy", "Test matrix", "Async lifecycle and lessons"],
    },
    {
        "number": 5,
        "phase": "Automation and integration",
        "title": "Choose Flow or Apex and integrate securely",
        "focus": "Connect lead intake, approvals, email automation, callouts, credentials, and REST services.",
        "estimated_time": "6 to 9 hours",
        "interview": "How do you choose between Flow and Apex, and how do you integrate Salesforce?",
        "competencies": ["Flow design", "Approvals", "API integration", "Integration security"],
        "steps": [
            step("Learn", ["Map the end-to-end process and integration boundaries.", "Identify authentication, limits, retry, and error requirements."], "An automation and integration map."),
            step("Build", ["Implement supported record-triggered Flows and approvals.", "Implement secure callout and REST patterns."], "Working automation and integration."),
            step("Prove", ["Test normal, bulk, invalid, timeout, and permission scenarios.", "Capture requests, responses, and resulting records."], "Integration test evidence."),
            step("Explain", ["Explain the Flow-versus-Apex choice.", "Walk through authentication, request, response, mapping, and failures."], "A sequence-diagram walkthrough."),
            step("Defend", ["Explain idempotency, retries, credential storage, and limits.", "Describe monitoring and operational support."], "A secure integration defense."),
            step("Improve", ["Remove hard-coded credentials and brittle mappings.", "Add actionable errors and operational logging."], "A supportable integration."),
        ],
        "knowledge_check": ["When should Flow call invocable Apex?", "Why use Named Credentials?", "How should an integration handle retry safely?"],
        "defense_questions": ["Why is this Flow rather than Apex?", "How do you avoid duplicate processing?", "How are secrets and errors handled?"],
        "presentation_topic": "Flow, approvals, callouts, and REST integrations",
        "presentation_slides": ["Automation problem", "Flow/Apex decision", "Integration sequence", "Security and failure handling", "Testing and result"],
    },
    {
        "number": 6,
        "phase": "User experience",
        "title": "Build LWC and Experience Cloud user journeys",
        "focus": "Present reusable components, data access, navigation, external security, responsive behavior, and accessibility.",
        "estimated_time": "6 to 9 hours",
        "interview": "Tell me about a Lightning Web Component you designed.",
        "competencies": ["LWC", "Lightning Data Service", "Experience Cloud", "UX quality"],
        "steps": [
            step("Learn", ["Map users, journeys, components, and data sources.", "Review Experience Cloud permission and sharing requirements."], "A component and journey map."),
            step("Build", ["Implement focused components with clear responsibilities.", "Configure external pages, targets, permissions, and navigation."], "Working internal and external experiences."),
            step("Prove", ["Test loading, error, empty, permission, guest, and responsive states.", "Capture user-journey evidence."], "A UX test package."),
            step("Explain", ["Explain UI Record API, LDS, Apex, events, and navigation choices.", "Demonstrate the complete user journey."], "A seven-minute walkthrough."),
            step("Defend", ["Explain external-user access and data exposure.", "Discuss accessibility, performance, and maintainability."], "A UX and security defense."),
            step("Improve", ["Simplify component responsibilities and state management.", "Improve labels, errors, empty states, keyboard use, and mobile layout."], "A polished experience."),
        ],
        "knowledge_check": ["When is Lightning Data Service preferable to Apex?", "What must be checked for guest-user access?", "What makes a component reusable?"],
        "defense_questions": ["Why did this component need Apex?", "How is data exposure controlled?", "What happens on slow or failed requests?"],
        "presentation_topic": "LWC components and Experience Cloud user journeys",
        "presentation_slides": ["User experience goal", "Component map", "Data access", "Main journey", "Security, errors, and improvements"],
    },
    {
        "number": 7,
        "phase": "Delivery",
        "title": "Present and deliver the complete solution",
        "focus": "Turn the project into a concise architecture story, tested demonstration, release package, and stakeholder presentation.",
        "estimated_time": "6 to 8 hours",
        "interview": "Present a Salesforce solution you designed and delivered.",
        "competencies": ["Architecture communication", "Demo delivery", "Release readiness", "Stakeholder communication"],
        "steps": [
            step("Learn", ["Review the solution as one end-to-end system.", "Identify the few decisions that matter most to the audience."], "A presentation strategy."),
            step("Build", ["Create an 8-10 slide deck, architecture diagram, and demonstration script.", "Prepare release notes and known limitations."], "A complete delivery package."),
            step("Prove", ["Run regression tests and a timed demonstration.", "Verify all links, data, permissions, and fallback steps."], "Release and demo evidence."),
            step("Explain", ["Lead with business value before technical detail.", "Show outcomes rather than a feature-by-feature tour."], "A clear project presentation."),
            step("Defend", ["Answer design, security, testing, scale, and improvement questions.", "Clearly distinguish implemented, simulated, and future work."], "A stakeholder-ready defense."),
            step("Improve", ["Remove crowded slides and unnecessary screenshots.", "Refine the demo based on peer and instructor feedback."], "A polished final presentation."),
        ],
        "knowledge_check": ["What belongs in a release-readiness checklist?", "How should a demo recover from failure?", "Which architecture decisions need explicit tradeoffs?"],
        "defense_questions": ["What is the most important design decision?", "What is not production-ready yet?", "How would you support this after launch?"],
        "presentation_topic": "Complete Salesforce project presentation",
        "presentation_slides": ["Business problem", "Users and requirements", "Architecture", "Key capabilities", "Testing and delivery", "Value and lessons"],
    },
    {
        "number": 8,
        "phase": "Interview readiness",
        "title": "Defend the project in a Salesforce interview",
        "focus": "Convert project evidence into strong technical, behavioral, business-analysis, and architecture answers.",
        "estimated_time": "5 to 7 hours",
        "interview": "What did you personally do, what was difficult, and what would you improve?",
        "competencies": ["Interview communication", "STAR stories", "Technical defense", "Career planning"],
        "steps": [
            step("Learn", ["Review common Admin, Developer, BA, and solution-design interview patterns.", "Identify where project evidence supports each answer."], "An interview topic map."),
            step("Build", ["Write ten project-based answers and five STAR stories.", "Create a 30-day learning and certification plan."], "An interview answer bank."),
            step("Prove", ["Attach evidence to every major claim.", "Complete a recorded mock interview."], "A mock-interview scorecard."),
            step("Explain", ["Answer with context, action, technical reasoning, result, and lesson.", "Keep answers specific and concise."], "Interview-ready responses."),
            step("Defend", ["Accept follow-up questions without changing the story.", "State uncertainty honestly and explain how you would verify it."], "Credible technical defense."),
            step("Improve", ["Prioritize weak technical areas and vague examples.", "Repeat the mock interview after corrections."], "A focused career plan."),
        ],
        "knowledge_check": ["What makes a project claim credible?", "How should you answer something you do not know?", "What is the difference between a task and an outcome?"],
        "defense_questions": ["What was the hardest technical problem?", "What mistake did you make and how did you correct it?", "What would you redesign with more time?"],
        "presentation_topic": "Interview defense of the project",
        "presentation_slides": ["60-second story", "Key design decision", "Hardest challenge", "Testing and quality", "Improvements", "Questions I can defend"],
    },
]

for week in CURRICULUM:
    week["presentation_requirement"] = (
        "Create a concise presentation using the suggested structure. Include evidence, explain design choices, "
        "identify your personal contribution, and prepare to answer the defense questions."
    )
