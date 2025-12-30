# **Project Specification: Gemini GovBid Pipeline**

## **1. Executive Summary**

- **Project Name:** Gemini GovBid Pipeline
- **Objective:** Develop a local desktop automation system that autonomously discovers, analyzes, and drafts proposals for government software contracts.
- **Core Technology:** Python, Google Gemini API (Free Tier), SQLite, Streamlit.
- **Deployment:** Local Windows Workstation.
- **Primary Goal:** Reduce manual search time by 95% by using AI to filter out irrelevant bids (e.g., construction, paving) and draft initial technical proposals for valid software opportunities.

---

## **2. System Architecture**

The system follows a **Local Microservices Architecture**. Independent components (services) run in parallel, communicating asynchronously via a shared SQLite database.

### **High-Level Diagram**

1. **Harvester Service:** Scans the web Downloads PDFs Saves to Disk/DB.
2. **Processor Service:** Reads DB Sends PDF to Gemini Flash Updates DB with Score.
3. **Dashboard (UI):** Reads DB Displays Leads Triggers Gemini Pro for Drafting.
4. **Orchestrator:** Manages the lifecycle (start/stop) of all services.

---

## **3. Component Specifications**

### **Module A: The Nervous System (Database Layer)**

- **Role:** The single source of truth for the application.
- **Technology:** SQLite with **Write-Ahead Logging (WAL)** enabled.
- **Concurrency Requirement:** Must support simultaneous reading (by UI) and writing (by Harvester/Processor) without locking errors.
- **Data Model (The "Bid" Entity):**
- **Metadata:** Unique ID, Title, URL, Source Authority, Creation Date.
- **Status Tracking:** Current state (Pending Downloaded Qualified Drafted Rejected).
- **File Management:** Local file path to the downloaded PDF.
- **AI Analysis:** Relevance Score (0-100), AI Reasoning (Why was it accepted/rejected?), Draft Content (The proposal text).

### **Module B: The Harvester (Ingestion Service)**

- **Role:** The "Gatherer." It creates the funnel of raw data.
- **Input Sources:** RSS Feeds (primary) and Direct Web Access (secondary fallback via Browser Automation).
- **Key Logic Flow:**

1. **Poll Feeds:** Connect to target government RSS feeds (e.g., CanadaBuys).
2. **Deduplication:** Check the database URL index to ensure the bid hasn't been processed already.
3. **Pre-Filter (Keyword):** Apply a fast, zero-cost keyword check (e.g., contain "software", "data", "system") to discard obvious junk like "asphalt" or "janitorial" before downloading.
4. **Download:** Retrieve the associated RFP document (PDF) and save it to the local `data/` folder.
5. **Record Creation:** Insert a new record into the database with status `downloaded`.

### **Module C: The Processor (AI Analysis Service)**

- **Role:** The "Filter." It separates the signal from the noise.
- **AI Model:** **Gemini 1.5 Flash** (Chosen for speed and low cost/free tier optimization).
- **Key Logic Flow:**

1. **Watch Queue:** Continuously poll the database for records with status `downloaded`.
2. **Upload:** Upload the local PDF file to the Gemini API temporary storage.
3. **Prompt Strategy:** Send a structured prompt asking the AI to:

- Determine if the contract is for _Custom Software Development_.
- Assign a relevance score (0-100).
- Provide a short reasoning string.
- Return the data in strict JSON format.

4. **Decision Engine:** Parse the JSON. If the score is above the threshold (e.g., 70), update status to `qualified`. Otherwise, set to `rejected`.
5. **Rate Limiter:** Enforce a strict sleep cycle (e.g., 4 seconds) between jobs to adhere to the Free Tier limit (15 Requests Per Minute).

### **Module D: The Drafter (Proposal Engine)**

- **Role:** The "Writer." It performs the high-value creative work.
- **AI Model:** **Gemini 1.5 Pro** (Chosen for higher reasoning capabilities and prose quality).
- **Trigger:** This is **not** automated. It is triggered manually by the user via the Dashboard to ensure API quotas are saved for high-value targets only.
- **Key Logic Flow:**

1. User clicks "Generate" on a qualified lead.
2. System retrieves the file path.
3. **Prompt Strategy:** Instruct the AI to act as a Senior Proposal Writer and generate a "Technical Approach" section based specifically on the requirements found in the document.
4. **Output:** Save the generated text into the `draft_content` field in the database and set status to `drafted`.

### **Module E: The Dashboard (User Interface)**

- **Role:** The Control Center.
- **Technology:** Streamlit.
- **Key Interface Elements:**
- **Metrics Bar:** Real-time counters for pending, qualified, and drafted bids.
- **Qualified Feed:** A list of "Green Light" opportunities. Each item is an expandable card showing:
- Title and Source.
- AI Relevance Score & Reasoning.
- "Generate Proposal" Action Button.

- **Drafts View:** A section to review, copy, or export the final generated text.
- **Rejection Log:** A transparent view of what the AI discarded (for auditing purposes).

### **Module F: The Orchestrator**

- **Role:** Process Management.
- **Function:** A single script that:

1. Starts the Harvester as a background process.
2. Starts the Processor as a background process.
3. Launches the Dashboard in the foreground.
4. Listens for a "Stop" command (Ctrl+C) and cleanly terminates all background processes to prevent memory leaks or orphaned scripts.

---

## **4. Implementation Roadmap**

### **Phase 1: Environment Setup**

1. Install Python 3.10+.
2. Obtain Google AI Studio API Key.
3. Configure local environment variables (security best practice).
4. Create the project directory structure.

### **Phase 2: Data Foundation**

1. Define the Database Schema code using the ORM (Object-Relational Mapping).
2. Write the initialization script to create the local SQLite database file.
3. Verify WAL mode is active to support concurrent read/writes.

### **Phase 3: The Ingestion Pipeline**

1. Write the Harvester logic to parse a sample RSS feed.
2. Implement the file download logic (handling file naming and storage).
3. Test the loop: Run Harvester Verify PDF appears in folder Verify Record appears in DB.

### **Phase 4: The Intelligence Layer**

1. Implement the Gemini Client connection.
2. Write the "Prompt Engineering" logic for the Processor.
3. Implement the JSON parser to convert AI text response into database updates.
4. **Critical:** Implement the Rate Limiter logic to prevent API errors.

### **Phase 5: The User Experience**

1. Build the Streamlit layout.
2. Connect the UI to the Database to display real-time rows.
3. Implement the "Generate Proposal" button logic.

### **Phase 6: Orchestration & Launch**

1. Write the Master Script to launch all components simultaneously.
2. Perform end-to-end testing:

- Trigger RSS update.
- Watch file download.
- Watch status change to `qualified` automatically.
- Click "Generate" and verify draft creation.

---

## **5. Risk Management & Constraints**

- **API Quotas:** The system relies on the Free Tier (15 RPM). The Processor **must** include a delay mechanism, or the API will return 429 Errors (Too Many Requests).
- **File Integrity:** Government filenames can be messy. The system must "sanitize" filenames (remove special characters) before saving to Windows to avoid path errors.
- **Concurrency:** If the Dashboard crashes with "Database Locked" errors, verify that the Database Module is correctly initializing `check_same_thread=False` and WAL mode.
