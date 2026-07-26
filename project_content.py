"""Default project and certification data for the Project Group portal."""

CERTIFICATIONS = [
    {"code": "ADMIN", "name": "Salesforce Certified Administrator", "short_name": "Admin cert.", "sort_order": 1},
    {"code": "PDI", "name": "Salesforce Certified Platform Developer I", "short_name": "Developer cert.", "sort_order": 2},
]

HR_PROJECT = {
    "name": "HR Management Application",
    "slug": "hr-management-application",
    "short_name": "HR Management App",
    "summary": (
        "A custom Salesforce application for managing job positions, candidates, interviewers, "
        "HR managers, office locations, recruitment activity, and public-facing experiences."
    ),
    "business_problem": (
        "Recruiters need one place to manage positions, candidates, interviewers, scheduling, "
        "communications, service requests, reporting, and external access."
    ),
    "users": "HR Managers\nCandidates\nInterviewers\nSystem Administrators\nPublic or Experience Cloud users",
    "objects": (
        "Location\nHR Manager\nPosition\nCandidate\nInterviewer\nPosition / Candidate\n"
        "Position / Interviewer\nError Log\nLead\nCase\nEmail Message"
    ),
    "outcomes": (
        "A working Recruitment Management Lightning application\n"
        "A controlled data and security model\n"
        "Declarative and Apex automation\n"
        "Address verification and REST integrations\n"
        "Reusable Lightning Web Components\n"
        "An Experience Cloud site and Email-to-Case workflow"
    ),
    "source_filename": "HR_Management_Application_Source.docx",
}

HR_PROJECT_STEPS = [
    {
        "step_number": 1,
        "phase": "Foundation",
        "title": "Object, application, validation, duplicate, and security setup",
        "summary": "Build the core data model and secure the application before automation begins.",
        "tasks": [
            "Create the Recruitment Management Lightning application.",
            "Create Location, HR Manager, Position, Candidate, Interviewer, junction, and Error Log objects and fields.",
            "Add field descriptions and help text.",
            "Create Position and Position/Interviewer validation rules.",
            "Create duplicate rules for Interviewer, Candidate, and HR Manager.",
            "Configure profiles or permission sets, roles, organization-wide defaults, and sharing rules.",
            "Create test data and verify access as different users.",
        ],
        "deliverables": [
            "Data model or ERD",
            "Object and field inventory",
            "Validation and duplicate-rule evidence",
            "Security matrix and test screenshots",
        ],
        "source_reference": "Source project pages 6-14, including Step 1, Steps 1.1-1.3, and the security tables.",
    },
    {
        "step_number": 2,
        "phase": "Foundation",
        "title": "Reports and dashboard",
        "summary": "Create basic operational visibility for positions and candidates.",
        "tasks": [
            "Create a Position-Candidate report showing candidate count by Position.",
            "Create a Position report showing Position count by year.",
            "Add both reports to a dashboard.",
            "Confirm filters, grouping, and chart labels are understandable.",
        ],
        "deliverables": ["Two reports", "One dashboard", "Screenshots and a short explanation of the business value"],
        "source_reference": "Source project page 15, Step 2.",
    },
    {
        "step_number": 3,
        "phase": "Apex",
        "title": "Position-Interviewer trigger and unit tests",
        "summary": "Prevent conflicting interviewer bookings and prove the logic with tests.",
        "tasks": [
            "Create a bulk-safe trigger on Position-Interviewer for before insert and before update.",
            "Prevent an interviewer from being assigned to conflicting or duplicate Positions.",
            "Move logic to a handler or helper class.",
            "Create tests using @TestSetup, Test.startTest, Test.stopTest, assertions, and negative cases.",
            "Achieve at least 90% coverage for the trigger and supporting class.",
        ],
        "deliverables": ["Trigger", "Handler/helper", "Unit test class", "Passing test and coverage evidence"],
        "source_reference": "Source project pages 15-16, Steps 3.1 and 3.2.",
    },
    {
        "step_number": 4,
        "phase": "Apex",
        "title": "Reusable Error Log service",
        "summary": "Centralize error recording so Apex processes can log consistent diagnostic information.",
        "tasks": [
            "Create a reusable Apex class for inserting Error Log records.",
            "Accept dynamic log date/time, details, process name, and optional class information.",
            "Design the method so other classes and triggers can reuse it.",
            "Add unit tests for successful and failure scenarios.",
        ],
        "deliverables": ["Reusable logging class", "Unit tests", "Example usage"],
        "source_reference": "Source project page 16, Step 4.",
    },
    {
        "step_number": 5,
        "phase": "Apex",
        "title": "Scheduled batch cleanup and completion email",
        "summary": "Automate retention cleanup for old completed Positions and notify the Daily Job group.",
        "tasks": [
            "Create a batch class that selects completed Positions more than two months old.",
            "Use a handler class for delete or cleanup logic.",
            "Send a finish-method email to users in the Daily Job public group.",
            "Create a schedulable class and schedule it for 3:00 AM daily.",
            "Document selection logic and safety controls.",
        ],
        "deliverables": ["Batch class", "Handler", "Schedulable class", "Public group and email evidence"],
        "source_reference": "Source project pages 16-17, Step 5.",
    },
    {
        "step_number": 6,
        "phase": "Apex",
        "title": "Batch Apex test",
        "summary": "Test the scheduled cleanup at realistic volume.",
        "tasks": [
            "Create at least 199 relevant records in the test context.",
            "Execute the batch inside Test.startTest and Test.stopTest.",
            "Assert eligible records are removed and ineligible records remain.",
            "Verify at least 85% coverage and successful test execution.",
        ],
        "deliverables": ["Batch test class", "Assertions", "Coverage and test-run evidence"],
        "source_reference": "Source project page 17, Step 6.",
    },
    {
        "step_number": 7,
        "phase": "Automation",
        "title": "Web-to-Lead, approval, and lead conversion automation",
        "summary": "Capture candidate and interviewer interest through a public form and route it correctly.",
        "tasks": [
            "Add Lead Type and Approved fields.",
            "Generate a Web-to-Lead form with contact information and type selection.",
            "Create interviewer approval and rejection email templates.",
            "Create an approval process for interviewer requests.",
            "Create record-triggered automation that creates a Candidate or routes an Interviewer for approval.",
            "Replace any legacy Process Builder requirement with supported record-triggered Flow where appropriate.",
        ],
        "deliverables": ["Working Web-to-Lead form", "Approval process", "Flows", "Email templates", "Test evidence"],
        "source_reference": "Source project pages 17-18, Step 7. The source mentions Process Builder; the portal flags this for instructor review because modern Salesforce implementations normally use Flow.",
    },
    {
        "step_number": 8,
        "phase": "Automation",
        "title": "Position-Candidate confirmation email Flow",
        "summary": "Confirm candidate registration with Position and location information.",
        "tasks": [
            "Create a record-triggered Flow on Position-Candidate.",
            "Build the confirmation subject and body using Candidate, Position, date, location, and HR Manager data.",
            "Include a Google Maps location link.",
            "Design and test for bulk record creation.",
        ],
        "deliverables": ["Flow", "Email template or text template", "Bulk test evidence"],
        "source_reference": "Source project pages 18-19, Step 8.",
    },
    {
        "step_number": 9,
        "phase": "Integration",
        "title": "Smarty address verification",
        "summary": "Verify Location addresses through Smarty and update the read-only verification result.",
        "tasks": [
            "Create secure authentication configuration for the Smarty API.",
            "Create reusable callout logic with error handling.",
            "Expose an invocable method for Flow.",
            "Map the response to the Location verification field.",
            "Test successful, invalid, and callout-failure scenarios with mocks.",
        ],
        "deliverables": ["Named Credential or secure auth setup", "Callout class", "Invocable method", "Flow", "Mock tests"],
        "source_reference": "Source project pages 19-20, Step 9.",
    },
    {
        "step_number": 10,
        "phase": "Integration",
        "title": "Position Apex REST service",
        "summary": "Expose eligible live Position details to external systems as JSON.",
        "tasks": [
            "Create an Apex REST resource.",
            "Return only live Positions with a start date after today.",
            "Use a stable JSON response structure and appropriate HTTP status handling.",
            "Test the resource with Workbench and Apex unit tests.",
        ],
        "deliverables": ["Apex REST class", "Unit tests", "Workbench request and response evidence"],
        "source_reference": "Source project page 20, Step 10.",
    },
    {
        "step_number": 11,
        "phase": "Lightning Web Components",
        "title": "Custom lookup and Position creation component",
        "summary": "Create reusable lookup behavior and a clean Position-entry experience.",
        "tasks": [
            "Create or adapt a reusable custom lookup LWC for Position, Interviewer, and Candidate relationships.",
            "Add the Position Detail rich-text field.",
            "Create a Position form using Lightning UI Record API rather than an Apex insert method.",
            "Redirect the user to the Position record after creation.",
            "Handle validation and user-facing errors.",
        ],
        "deliverables": ["Custom lookup LWC", "Position creation LWC", "Navigation and error-handling evidence"],
        "source_reference": "Source project pages 20-22, Steps 11.2 and 11.3. Step 11.1 is marked ignored in the source.",
    },
    {
        "step_number": 12,
        "phase": "Lightning Web Components",
        "title": "Position Detail workspace",
        "summary": "Present Position, Interviewer, Location, and Candidate information in one tabbed workspace.",
        "tasks": [
            "Create tabs for Position, Interviewer, Location, and Candidate details.",
            "Use Lightning Data Service for Position data where appropriate.",
            "Display related Interviewers and Candidates in data tables.",
            "Add New Interviewer and New Candidate actions with default Position values.",
            "Add Profile URL and About Me fields to Interviewer where required.",
        ],
        "deliverables": ["Tabbed Position Detail LWC", "Related-data queries", "Navigation actions", "Screenshots"],
        "source_reference": "Source project pages 22-24, Step 12 and its modification notes.",
    },
    {
        "step_number": 13,
        "phase": "Lightning Web Components",
        "title": "Live Position list and search",
        "summary": "Show eligible Positions in a searchable data table and navigate to details.",
        "tasks": [
            "Display live Positions whose start date is today or later.",
            "Make Position names navigable to record details.",
            "Add search by name, start date, and location.",
            "Handle empty results, errors, and loading states.",
        ],
        "deliverables": ["Position list LWC", "Search behavior", "Navigation and test evidence"],
        "source_reference": "Source project pages 25-26, Step 13.",
    },
    {
        "step_number": 14,
        "phase": "Lightning Web Components",
        "title": "Candidate Position membership component",
        "summary": "Show upcoming and past Positions for a Candidate and support new memberships.",
        "tasks": [
            "Create Upcoming Positions and Past Positions sections.",
            "Show only eligible upcoming Positions for selection.",
            "Prevent duplicate membership selection.",
            "Insert selected Position-Candidate records.",
            "Display past membership records as read-only data.",
        ],
        "deliverables": ["Candidate Position LWC", "Upcoming and past tables", "Membership creation evidence"],
        "source_reference": "Source project page 26, Step 14.",
    },
    {
        "step_number": 15,
        "phase": "Flow and LWC",
        "title": "Screen Flow with membership data table",
        "summary": "Allow users to add or clear Candidate membership through a guided screen flow.",
        "tasks": [
            "Create an Edit Position action on Candidate that opens a Screen Flow.",
            "Add Clear Membership and Add Membership choices.",
            "Use a data-table component to display current or eligible Positions.",
            "Delete deselected memberships or insert selected memberships.",
            "Close or finish the flow cleanly after success.",
        ],
        "deliverables": ["Screen Flow", "Data-table component configuration", "Add and clear membership test evidence"],
        "source_reference": "Source project page 27, Step 15.",
    },
    {
        "step_number": 16,
        "phase": "Experience Cloud",
        "title": "Experience Cloud foundation",
        "summary": "Create the external HR experience and configure profiles, navigation, and permissions.",
        "tasks": [
            "Enable and create the HR Experience Cloud site.",
            "Choose an appropriate current template.",
            "Create HR Manager and HR Candidate external-access profiles or permission sets.",
            "Configure object and field access based on the source matrix.",
            "Add required custom-object navigation items.",
        ],
        "deliverables": ["Experience Cloud site", "External-user access model", "Navigation and permission evidence"],
        "source_reference": "Source project pages 27-29, Step 16. The source uses the older term Community Cloud.",
    },
    {
        "step_number": 17,
        "phase": "Experience Cloud",
        "title": "Experience design and navigation",
        "summary": "Make the external experience clear and usable.",
        "tasks": [
            "Add a branded header and footer.",
            "Place Position list, calendar, and activity components where useful.",
            "Use consistent labels, spacing, and responsive layouts.",
            "Test navigation as guest and authenticated external users.",
        ],
        "deliverables": ["Updated site theme", "Page layouts", "Responsive and access test screenshots"],
        "source_reference": "Source project page 29, Step 17.",
    },
    {
        "step_number": 18,
        "phase": "Experience Cloud",
        "title": "Position and Candidate components in Experience Cloud",
        "summary": "Expose record-specific LWC experiences safely on external pages.",
        "tasks": [
            "Update target configurations for Experience Cloud use.",
            "Create custom Position and Candidate pages.",
            "Add PositionDetails and CandidatesPositions components.",
            "Configure CSP Trusted Sites and image access where required.",
            "Verify guest and external-user field permissions.",
        ],
        "deliverables": ["Experience-enabled LWCs", "Custom pages", "CSP and permission evidence"],
        "source_reference": "Source project pages 29-30, Step 18.",
    },
    {
        "step_number": 19,
        "phase": "Service Cloud",
        "title": "Email-to-Case and follow-up notification",
        "summary": "Capture service emails as Cases and alert owners when customers reply.",
        "tasks": [
            "Configure Email-to-Case and mail forwarding.",
            "Create the Email Cases queue and add users.",
            "Exchange test emails and verify Email Message records.",
            "Create a record-triggered Flow that sends a custom notification for a new customer Email Message on an open Case.",
            "Test threading, assignment, and notification behavior.",
        ],
        "deliverables": ["Email-to-Case configuration", "Queue", "Notification Flow", "End-to-end email evidence"],
        "source_reference": "Source project pages 30-31, Step 19.",
    },
]
