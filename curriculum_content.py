"""Simple eight-week project and interview curriculum."""

RUBRIC = [
    {"key": "business", "label": "Business understanding", "max_score": 20, "description": "Explains users, problem, scope, and business value."},
    {"key": "evidence", "label": "Evidence and completeness", "max_score": 20, "description": "Provides clear artifacts, examples, and complete deliverables."},
    {"key": "salesforce", "label": "Salesforce reasoning", "max_score": 20, "description": "Connects the work to appropriate Salesforce design and implementation choices."},
    {"key": "communication", "label": "Communication", "max_score": 20, "description": "Explains the work clearly and in an interview-ready structure."},
    {"key": "professionalism", "label": "Professional quality", "max_score": 20, "description": "Organizes the submission, responds to feedback, and presents accurate ownership."},
]


def guide_step(title, actions, output):
    return {"title": title, "actions": actions, "output": output}


CURRICULUM = [
    {
        "number": 1,
        "phase": "Understand",
        "title": "Know the project before you explain it",
        "focus": "Build a truthful project baseline and identify exactly what you completed.",
        "estimated_time": "3 to 5 hours",
        "interview": "Tell me about the Salesforce project you worked on.",
        "deliverables": ["Project summary", "Ownership checklist", "Evidence inventory", "60-second introduction"],
        "steps": [
            guide_step("Read the project brief", ["Read the project overview, users, objects, and all project steps.", "Write the business problem in your own words.", "List the people who use the solution."], "A one-paragraph project summary."),
            guide_step("Check your real work", ["List what you built, tested, researched, documented, or presented.", "Separate your work from work completed by teammates.", "Remove anything you cannot explain."], "An honest ownership checklist."),
            guide_step("Collect proof", ["Collect screenshots, diagrams, GitHub links, test results, and presentation slides.", "Label every item with the requirement it proves."], "A project evidence folder and inventory."),
            guide_step("Practice the opening", ["Use this order: business problem, users, your role, main solution, result, lesson.", "Record a 60-second answer twice and improve it."], "A final written and recorded introduction."),
        ],
        "quality_gate": ["I can explain the project without reading.", "I clearly identify my personal contribution.", "Every important claim has evidence."],
    },
    {
        "number": 2,
        "phase": "Requirements",
        "title": "Turn the project brief into clear requirements",
        "focus": "Understand stakeholders, process, scope, business rules, and acceptance criteria.",
        "estimated_time": "4 to 6 hours",
        "interview": "How do you gather and clarify requirements?",
        "deliverables": ["Stakeholder map", "Discovery questions", "User stories", "Acceptance criteria"],
        "steps": [
            guide_step("Identify stakeholders", ["List HR Managers, Candidates, Interviewers, administrators, and external users.", "Write what each user needs to do and what data they need."], "A stakeholder and access map."),
            guide_step("Find the business rules", ["Review validation, duplicate, scheduling, approval, integration, and notification requirements.", "Mark unclear or conflicting requirements."], "A business-rule list and open-question log."),
            guide_step("Write user stories", ["Create at least five user stories using As a / I want / So that.", "Add one exception or constraint to each story."], "Five testable user stories."),
            guide_step("Write acceptance criteria", ["Use Given / When / Then for normal and error paths.", "Include data, security, duplicate, and integration failures."], "Acceptance criteria for the selected stories."),
        ],
        "quality_gate": ["Requirements describe business outcomes, not only features.", "I identified exceptions and security needs.", "A tester can determine pass or fail."],
    },
    {
        "number": 3,
        "phase": "Foundation",
        "title": "Explain the data, security, and declarative foundation",
        "focus": "Connect the object model, access model, validation, duplicate management, reports, and dashboard.",
        "estimated_time": "4 to 6 hours",
        "interview": "How did you design the data model and security?",
        "deliverables": ["ERD", "Security matrix", "Rule inventory", "Dashboard explanation"],
        "steps": [
            guide_step("Draw the data model", ["Show core objects and both junction objects.", "Explain why each relationship is lookup or master-detail."], "A clean ERD and relationship explanation."),
            guide_step("Explain access", ["Map create, read, edit, delete needs by user type.", "Explain OWD, role hierarchy, sharing, and field access."], "A simplified security matrix."),
            guide_step("Document data quality", ["List validation and duplicate rules.", "Write the user problem each rule prevents."], "A rule inventory with business reasons."),
            guide_step("Explain reporting", ["Describe the candidate-by-position and positions-by-year reports.", "Explain what management can decide from the dashboard."], "A two-minute dashboard explanation."),
        ],
        "quality_gate": ["I can defend every relationship.", "I can explain record access separately from object and field access.", "I connect rules and reports to business value."],
    },
    {
        "number": 4,
        "phase": "Development",
        "title": "Explain Apex, bulk design, and testing",
        "focus": "Use the trigger, error logger, batch, schedulable, and tests to demonstrate developer thinking.",
        "estimated_time": "5 to 7 hours",
        "interview": "Describe an Apex solution you built and how you tested it.",
        "deliverables": ["Trigger design", "Test matrix", "Batch explanation", "Code-review notes"],
        "steps": [
            guide_step("Explain the trigger", ["State the object and trigger events.", "Explain duplicate or conflicting interviewer prevention.", "Show how the handler keeps logic bulk-safe."], "A trigger flow diagram and explanation."),
            guide_step("Explain testing", ["Document positive, negative, bulk, and update cases.", "Show @TestSetup, startTest/stopTest, and meaningful assertions."], "A test-case matrix."),
            guide_step("Explain reusable logging", ["Describe the Error Log service inputs and reuse pattern.", "Explain how failures are diagnosed without hiding errors."], "An error-handling design note."),
            guide_step("Explain batch and schedule", ["Explain selection criteria, execute behavior, finish email, and daily schedule.", "Describe the 199-record test and safety checks."], "A batch lifecycle explanation."),
        ],
        "quality_gate": ["I can explain bulkification without memorized definitions.", "My tests prove behavior, not only coverage.", "I can describe why the design is maintainable."],
    },
    {
        "number": 5,
        "phase": "Automation and integration",
        "title": "Explain Flow, approvals, callouts, and APIs",
        "focus": "Connect lead intake, approvals, email automation, address verification, and REST exposure.",
        "estimated_time": "5 to 7 hours",
        "interview": "How do you choose between Flow and Apex, and how do you integrate Salesforce?",
        "deliverables": ["Automation map", "Integration sequence diagram", "Failure-handling plan", "Research note"],
        "steps": [
            guide_step("Map the lead process", ["Show Web-to-Lead, Candidate creation, Interviewer approval, and notification outcomes.", "Identify where modern Flow replaces legacy Process Builder."], "A lead and approval process map."),
            guide_step("Explain confirmation email Flow", ["Show the trigger, related data, text template, bulk design, and result."], "A Flow explanation with sample email."),
            guide_step("Explain Smarty verification", ["Show authentication, request, response mapping, invocable method, Flow, and mock tests.", "Explain error handling and secure credential storage."], "An integration sequence diagram."),
            guide_step("Explain Apex REST", ["Describe endpoint behavior, filters, JSON contract, status handling, and tests."], "A sample request and response plus design notes."),
        ],
        "quality_gate": ["I can justify Flow versus Apex.", "I explain credentials and error handling securely.", "I can describe the full request and response lifecycle."],
    },
    {
        "number": 6,
        "phase": "User experience",
        "title": "Explain the LWC and Experience Cloud solution",
        "focus": "Present the custom lookup, record forms, detail workspace, search, membership, and external experience.",
        "estimated_time": "5 to 7 hours",
        "interview": "Tell me about a Lightning Web Component you designed.",
        "deliverables": ["Component map", "Data-flow notes", "UX walkthrough", "Security checklist"],
        "steps": [
            guide_step("Map the components", ["List the custom lookup, Position form, Position detail, Position list, Candidate Position, and data-table Flow components.", "Write the responsibility and inputs for each."], "A component architecture map."),
            guide_step("Explain data access", ["Identify UI Record API, Lightning Data Service, Apex, navigation, and related-record queries.", "Explain why each approach is used."], "A component data-access table."),
            guide_step("Walk through user journeys", ["Demonstrate creating a Position, opening details, searching, adding Interviewers or Candidates, and changing memberships."], "A seven-minute user journey script."),
            guide_step("Explain external access", ["Describe Experience Cloud pages, profiles or permission sets, CSP, guest access, and component targets."], "An Experience Cloud access checklist."),
        ],
        "quality_gate": ["Each component has one clear responsibility.", "I can explain data access and navigation choices.", "I consider accessibility, errors, empty states, and security."],
    },
    {
        "number": 7,
        "phase": "Presentation",
        "title": "Build a project presentation that tells one clear story",
        "focus": "Turn the project into a concise business and technical presentation.",
        "estimated_time": "4 to 6 hours",
        "interview": "Present a Salesforce solution you designed.",
        "deliverables": ["8-10 slide deck", "Architecture visual", "Demo script", "Q&A list"],
        "steps": [
            guide_step("Choose the story", ["Use this flow: problem, users, requirements, solution, architecture, key features, testing, result, lessons.", "Remove details that do not support the story."], "A one-page presentation outline."),
            guide_step("Build the visuals", ["Create an ERD, automation or integration diagram, and component map.", "Use screenshots only when they prove an outcome."], "Three clean supporting visuals."),
            guide_step("Create the deck", ["Keep each slide focused on one message.", "Use short labels and explain detail verbally.", "Clearly label personal contributions."], "A complete 8-10 slide deck."),
            guide_step("Practice delivery", ["Practice a seven-minute version and a three-minute version.", "Prepare answers for design choices, challenges, testing, and improvements."], "Recorded practice and Q&A preparation."),
        ],
        "quality_gate": ["The business problem appears before technical detail.", "Slides are visual and readable.", "I explain my contribution and decisions clearly."],
    },
    {
        "number": 8,
        "phase": "Interview readiness",
        "title": "Defend the project in a Salesforce interview",
        "focus": "Convert the project into strong behavioral, admin, developer, and solution-design answers.",
        "estimated_time": "4 to 6 hours",
        "interview": "What did you personally do, what was difficult, and what would you improve?",
        "deliverables": ["10 interview answers", "STAR stories", "Mock interview scorecard", "30-day plan"],
        "steps": [
            guide_step("Prepare core answers", ["Write answers for project overview, requirements, data model, security, automation, Apex, integration, LWC, testing, and deployment."], "Ten project-based interview answers."),
            guide_step("Prepare behavioral stories", ["Create STAR stories for a challenge, mistake, disagreement, research task, and improvement."], "Five behavioral stories."),
            guide_step("Run the mock interview", ["Answer without reading.", "Ask the interviewer to challenge design decisions and ownership.", "Score clarity, specificity, accuracy, and confidence."], "A completed mock-interview scorecard."),
            guide_step("Close the gaps", ["List weak technical areas, missing evidence, and unclear answers.", "Create a 30-day certification and interview-practice plan."], "A prioritized improvement plan."),
        ],
        "quality_gate": ["I answer with specific project evidence.", "I never present training as paid experience.", "I can defend choices and discuss improvements honestly."],
    },
]

PRESENTATION_GUIDES = {
    1: {
        "topic": "Introduce the project and your real contribution",
        "slides": ["Project and business problem", "Users and process", "What I personally worked on", "Evidence of my work", "What I learned and would improve"],
    },
    2: {
        "topic": "Requirements, stakeholders, user stories, and acceptance criteria",
        "slides": ["Business request", "Stakeholders", "Key requirements and rules", "User stories", "Acceptance criteria and open questions"],
    },
    3: {
        "topic": "Data model, security, data quality, reports, and dashboards",
        "slides": ["Object model and ERD", "Relationship decisions", "Security model", "Validation and duplicate rules", "Reports, dashboard, and business value"],
    },
    4: {
        "topic": "Apex design, bulkification, error handling, batch Apex, and testing",
        "slides": ["Technical requirement", "Trigger and handler design", "Bulk and error-handling strategy", "Test scenarios and results", "Batch lifecycle and lessons"],
    },
    5: {
        "topic": "Flow, approvals, callouts, and REST integrations",
        "slides": ["Automation problem", "Flow or Apex decision", "Integration sequence", "Security and failure handling", "Result and testing"],
    },
    6: {
        "topic": "LWC components and Experience Cloud user journeys",
        "slides": ["User experience goal", "Component map", "Data access and navigation", "Main user journey", "Security, errors, and improvements"],
    },
    7: {
        "topic": "Complete Salesforce project presentation",
        "slides": ["Business problem", "Users and requirements", "Solution architecture", "Key features", "Testing and delivery", "Value, contribution, and lessons"],
    },
    8: {
        "topic": "Interview defense of the project",
        "slides": ["60-second project story", "Most important design decision", "Hardest challenge", "Testing and quality", "What I would improve", "Questions I can confidently answer"],
    },
}

for week in CURRICULUM:
    presentation = PRESENTATION_GUIDES[week["number"]]
    week["presentation_topic"] = presentation["topic"]
    week["presentation_slides"] = presentation["slides"]
    week["presentation_requirement"] = (
        "Create and upload a short presentation about this week's project work. "
        "Use the suggested slide structure, include evidence, and clearly identify your personal contribution."
    )
