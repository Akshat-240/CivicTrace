export const mockStats = {
  criticalHigh: 18,
  openIncidents: 42,
  slaAtRisk: 11,
  verificationPending: 7,
  slaMetrics: {
    onTrack: 96,
    dueSoon: 11,
    overdue: 5,
    humanReview: 7
  },
  recentActivity: [
    "2 assignments created today",
    "3 resolution reviews completed",
    "1 case escalated to zone officer"
  ]
};

export const mockIncidents = [
  {
    id: "CT-INC-024",
    title: "Large pothole on MG Road",
    shortTitle: "Pothole",
    category: "Road",
    zone: "Hazratganj",
    location: "Hazratganj, MG Road",
    subLocation: "Near GPO Junction",
    priority: "HIGH",
    status: "In Progress",
    slaRemaining: "18h remaining",
    assignedTeam: "Road Team 04",
    reportedAt: "2026-09-12 09:30",
    description: "Deep pothole causing significant traffic slowdown and accident hazard during peak hours.",
    coordinates: { top: "35%", left: "28%" },
    evidence: {
      submittedBy: "Road Team 04",
      before: "Pothole detected",
      after: "Repair visible",
      aiConfidence: 96,
      aiResolution: "Partial resolution"
    }
  },
  {
    id: "CT-INC-021",
    title: "Main line water leakage",
    shortTitle: "Water leakage",
    category: "Water",
    zone: "Aliganj",
    location: "Aliganj, Sector C",
    subLocation: "Kapoorthala Chauraha",
    priority: "CRITICAL",
    status: "Assigned",
    slaRemaining: "2h remaining",
    assignedTeam: "Water Team 02",
    reportedAt: "2026-09-12 11:15",
    description: "Underground water pipeline burst with high volume water loss flooding primary road.",
    coordinates: { top: "28%", left: "75%" },
    evidence: null
  },
  {
    id: "CT-INC-019",
    title: "Streetlight not working",
    shortTitle: "Streetlight not working",
    category: "Electrical",
    zone: "Gomti Nagar",
    location: "Gomti Nagar, Viram Khand",
    subLocation: "Main Boulevard",
    priority: "MEDIUM",
    status: "Awaiting Verification",
    slaRemaining: "31h remaining",
    assignedTeam: "Electrical Team 01",
    reportedAt: "2026-09-11 18:40",
    description: "Series of 4 streetlights dark creating unsafe pedestrian stretch near community park.",
    coordinates: { top: "58%", left: "55%" },
    evidence: {
      submittedBy: "Electrical Team 01",
      before: "Dark streetlight row",
      after: "Bulbs replaced and powered",
      aiConfidence: 98,
      aiResolution: "Full resolution"
    }
  },
  {
    id: "CT-INC-017",
    title: "Garbage accumulation",
    shortTitle: "Garbage accumulation",
    category: "Sanitation",
    zone: "Indira Nagar",
    location: "Indira Nagar, Block B",
    subLocation: "Market back alley",
    priority: "HIGH",
    status: "Open",
    slaRemaining: "7h remaining",
    assignedTeam: null,
    reportedAt: "2026-09-12 14:05",
    description: "Solid waste overflow around municipal bin blocking half the service lane.",
    coordinates: { top: "72%", left: "32%" },
    evidence: null
  },
  {
    id: "CT-INC-016",
    title: "Broken drain cover",
    shortTitle: "Broken drain cover",
    category: "Road",
    zone: "Mahanagar",
    location: "Mahanagar, Gol Market",
    subLocation: "Near Metro station pillar 42",
    priority: "MEDIUM",
    status: "Open",
    slaRemaining: "24h remaining",
    assignedTeam: null,
    reportedAt: "2026-09-12 08:20",
    description: "Heavy concrete manhole slab cracked open, immediate danger to two-wheelers.",
    coordinates: { top: "70%", left: "80%" },
    evidence: null
  }
];

export const mockTeamLoads = [
  { name: "Road Team 04", active: 8, color: "#2563EB" },
  { name: "Water Team 02", active: 5, color: "#16A34A" },
  { name: "Electrical Team 01", active: 4, color: "#EA580C" },
  { name: "Sanitation Team 03", active: 6, color: "#2563EB" }
];

export const mockAvailableOfficers = [
  { id: "OFF-101", name: "Rajesh Sharma", department: "Road Infrastructure", currentAssignments: 2 },
  { id: "OFF-102", name: "Amit Verma", department: "Water Supply & Sewage", currentAssignments: 1 },
  { id: "OFF-103", name: "Priya Singh", department: "Sanitation & Solid Waste", currentAssignments: 3 },
  { id: "OFF-104", name: "Sunil Tiwari", department: "Electrical Works", currentAssignments: 1 }
];

export const mockSlaMonitor = {
  critical: "2 due soon",
  high: "6 due soon",
  medium: "8 on track",
  overdue: "5 cases"
};

// ==========================================
// ADMIN PORTAL MOCK DATA
// ==========================================

export const mockAdminStats = {
  critical: 18,
  high: 47,
  open: 132,
  slaCompliance: "91%",
  citizenRating: "4.8/5"
};

export const mockAdminIncidents = [
  {
    id: "#CT-1842",
    rawId: "CT-1842",
    issue: "Pothole",
    category: "Road Damage",
    location: "Faizabad Road",
    ward: "Ward 12",
    zone: "East Zone",
    priority: "High",
    status: "Open",
    reported: "2h ago",
    department: "Roads Department",
    sla: "2h remaining",
    slaRisk: true
  },
  {
    id: "#CT-1839",
    rawId: "CT-1839",
    issue: "Garbage Overflow",
    category: "Sanitation",
    location: "Aliganj",
    ward: "Ward 8",
    zone: "North Zone",
    priority: "Critical",
    status: "In Progress",
    reported: "5h ago",
    department: "Sanitation Department",
    sla: "SLA breached",
    slaRisk: true,
    slaBreached: true
  },
  {
    id: "#CT-1831",
    rawId: "CT-1831",
    issue: "Streetlight Not Working",
    category: "Streetlight",
    location: "Indira Nagar",
    ward: "Ward 6",
    zone: "East Zone",
    priority: "Medium",
    status: "In Progress",
    reported: "1d ago",
    department: "Electrical Department",
    sla: "6h remaining",
    slaRisk: false
  },
  {
    id: "#CT-1827",
    rawId: "CT-1827",
    issue: "Water Leakage",
    category: "Water Supply",
    location: "Gomti Nagar",
    ward: "Ward 14",
    zone: "Central Zone",
    priority: "High",
    status: "Open",
    reported: "1d ago",
    department: "Water Supply",
    sla: "11h remaining",
    slaRisk: true
  },
  {
    id: "#CT-1819",
    rawId: "CT-1819",
    issue: "Fallen Tree",
    category: "Environment",
    location: "Hazratganj",
    ward: "Ward 3",
    zone: "Central Zone",
    priority: "Medium",
    status: "Resolved",
    reported: "2d ago",
    department: "Environment",
    sla: "Resolved",
    slaRisk: false
  },
  {
    id: "#CT-1812",
    rawId: "CT-1812",
    issue: "Drainage Blockage",
    category: "Drainage",
    location: "Mahanagar",
    ward: "Ward 10",
    zone: "Central Zone",
    priority: "High",
    status: "In Progress",
    reported: "2d ago",
    department: "Sanitation Department",
    sla: "18h remaining",
    slaRisk: false
  },
  {
    id: "#CT-1805",
    rawId: "CT-1805",
    issue: "Construction Waste",
    category: "Solid Waste",
    location: "Jankipuram",
    ward: "Ward 15",
    zone: "North Zone",
    priority: "Low",
    status: "Open",
    reported: "3d ago",
    department: "Sanitation Department",
    sla: "32h remaining",
    slaRisk: false
  },
  {
    id: "#CT-1798",
    rawId: "CT-1798",
    issue: "Stray Dogs",
    category: "Public Safety",
    location: "Alambagh",
    ward: "Ward 18",
    zone: "South Zone",
    priority: "Medium",
    status: "In Progress",
    reported: "3d ago",
    department: "Public Safety",
    sla: "28h remaining",
    slaRisk: false
  }
];

export const mockIncidentDetailCT1842 = {
  id: "#CT-1842",
  rawId: "CT-1842",
  title: "Pothole",
  subtitle: "Large pothole causing traffic issues near Faizabad Road.",
  priority: "High",
  status: "Open",
  location: "Faizabad Road, Lucknow",
  ward: "Ward 12",
  zone: "East Zone",
  reportedTime: "Reported 2 hours ago",
  reportedDate: "12 Sept 2024, 08:14 AM",
  description: "A large pothole on Faizabad Road near the university gate is causing traffic issues and is dangerous for two-wheelers and low-height vehicles.",
  coordinates: {
    lat: 26.8951,
    long: 81.0154,
    zone: "Zone East"
  },
  evidence: [
    { id: 1, label: "REPORTED PHOTO", caption: "Initial complaint evidence photo", timestamp: "12 Sept 2024, 08:14 AM" },
    { id: 2, label: "ANGLE 2", caption: "Close-up of crater depth", timestamp: "12 Sept 2024, 08:14 AM" },
    { id: 3, label: "CONTEXT VIEW", caption: "Traffic perspective", timestamp: "12 Sept 2024, 08:15 AM" }
  ],
  aiAnalysis: {
    detectedIssue: "Pothole",
    severity: "High",
    confidence: "High",
    confidenceScore: "92%",
    objects: "pothole 0.94 · road 0.91 · vehicle 0.62",
    summary: "Large surface pothole detected with clear structural damage. Likely hazardous for two-wheelers."
  },
  duplicates: [
    { id: "#CT-1831", match: "75% match · 500m away", status: "Merged", color: "#16A34A" },
    { id: "#CT-1804", match: "62% match · 1.2km away", status: "Related", color: "#2563EB" }
  ],
  responsibleAuthority: {
    department: "Roads Department",
    org: "Lucknow Municipal Corporation",
    nodalOfficer: "Rohit Rai",
    phone: "+91 98765 43210",
    email: "rohit.rai@lmc.gov.in"
  },
  auditTimeline: [
    { time: "08:14 AM", event: "Incident Reported", user: "Citizen" },
    { time: "08:15 AM", event: "AI Analysis Completed", user: "CivicTrace AI Engine" },
    { time: "08:20 AM", event: "Authority Routed", user: "Auto-dispatcher" },
    { time: "09:10 AM", event: "Status Updated to Open", user: "Rohit Rai (Roads Dept)" }
  ]
};

export const mockAdminMapPins = [
  { id: "#CT-1842", issue: "Pothole", location: "Faizabad Road • Ward 12", priority: "Critical", status: "ACTIVE", tag: "HIGH • SLA AT RISK • RESOLUTION CHECK PENDING", x: 62, y: 44 },
  { id: "#CT-1839", issue: "Garbage Overflow", location: "Aliganj • Ward 8", priority: "Critical", status: "BREACHED", tag: "CRITICAL • SLA OVERDUE", x: 28, y: 35 },
  { id: "#CT-1831", issue: "Streetlight Dark", location: "Indira Nagar • Ward 6", priority: "Medium", status: "ASSIGNED", tag: "MEDIUM • ON TRACK", x: 74, y: 32 },
  { id: "#CT-1827", issue: "Water Leakage", location: "Gomti Nagar • Ward 14", priority: "High", status: "IN PROGRESS", tag: "HIGH • 11h REMAINING", x: 50, y: 72 },
  { id: "#CT-1819", issue: "Fallen Tree", location: "Hazratganj • Ward 3", priority: "Resolved", status: "RESOLVED", tag: "RESOLVED • EVIDENCE VERIFIED", x: 40, y: 55 },
  { id: "#CT-1812", issue: "Drainage Blockage", location: "Mahanagar • Ward 10", priority: "High", status: "IN PROGRESS", tag: "HIGH • 18h REMAINING", x: 80, y: 60 },
  { id: "#CT-1805", issue: "Solid Waste", location: "Jankipuram • Ward 15", priority: "Low", status: "OPEN", tag: "LOW • 32h REMAINING", x: 22, y: 65 },
  { id: "#CT-1798", issue: "Public Safety", location: "Alambagh • Ward 18", priority: "Medium", status: "ASSIGNED", tag: "MEDIUM • 28h REMAINING", x: 88, y: 42 }
];

export const mockAdminAnalytics = {
  totalIncidents: 284,
  resolved: 196,
  slaBreached: 23,
  slaCompliance: "91%",
  verifiedResolution: "92%",
  categoryMix: [
    { label: "Road Damage", count: 64, color: "#2563EB" },
    { label: "Sanitation", count: 48, color: "#10B981" },
    { label: "Water Supply", count: 42, color: "#06B6D4" },
    { label: "Streetlight", count: 37, color: "#F59E0B" },
    { label: "Other", count: 93, color: "#6B7280" }
  ],
  hotspots: [
    { ward: "Ward 12", incidents: 24 },
    { ward: "Ward 8", incidents: 19 },
    { ward: "Ward 14", incidents: 17 }
  ],
  trendData: [
    { date: "1 Sep", reported: 28, resolved: 14 },
    { date: "4 Sep", reported: 24, resolved: 16 },
    { date: "7 Sep", reported: 32, resolved: 12 },
    { date: "10 Sep", reported: 21, resolved: 18 },
    { date: "13 Sep", reported: 30, resolved: 22 },
    { date: "16 Sep", reported: 28, resolved: 24 },
    { date: "19 Sep", reported: 22, resolved: 19 },
    { date: "22 Sep", reported: 38, resolved: 26 },
    { date: "25 Sep", reported: 34, resolved: 31 },
    { date: "30 Sep", reported: 39, resolved: 33 }
  ],
  departmentPerformance: [
    { name: "Roads Department", resolution: "88%", sla: "94%", open: 31 },
    { name: "Sanitation Department", resolution: "82%", sla: "89%", open: 38 },
    { name: "Water Supply", resolution: "79%", sla: "86%", open: 27 }
  ]
};

export const mockAdminSLAPage = {
  rules: [
    { priority: "CRITICAL", response: "2h", resolution: "6h", escalation: "Zone", color: "#EF4444" },
    { priority: "HIGH", response: "4h", resolution: "24h", escalation: "Dept.", color: "#F97316" },
    { priority: "MEDIUM", response: "8h", resolution: "3d", escalation: "Dept.", color: "#EAB308" },
    { priority: "LOW", response: "24h", resolution: "7d", escalation: "Dept.", color: "#3B82F6" }
  ],
  escalationPath: [
    { level: "L1", title: "Department Officer", desc: "First response & field dispatch" },
    { level: "L2", title: "Zone Officer", desc: "Escalated if 50% SLA elapsed without action" },
    { level: "L3", title: "Municipal Officer", desc: "Immediate review on SLA breach" },
    { level: "L4", title: "Higher Authority", desc: "Administrative penalty & governance review" }
  ],
  evidenceDecisions: [
    { state: "FULLY_RESOLVED", label: "Closes incident & meets SLA", color: "#10B981" },
    { state: "PARTIALLY_RESOLVED", label: "Requires follow-up verification", color: "#F59E0B" },
    { state: "INSUFFICIENT_EVIDENCE", label: "Triggers escalation & re-inspection", color: "#EF4444" }
  ]
};

export const mockAdminDepartments = [
  { id: 1, name: "Roads Department", assigned: 284, resolved: 252, sla: "94%", open: 32, nodalOfficer: "Rohit Rai", zone: "Central & East" },
  { id: 2, name: "Sanitation Department", assigned: 216, resolved: 188, sla: "89%", open: 28, nodalOfficer: "Anita Verma", zone: "All Wards" },
  { id: 3, name: "Electrical Department", assigned: 173, resolved: 166, sla: "96%", open: 7, nodalOfficer: "Vivek Singh", zone: "North & East" },
  { id: 4, name: "Water Supply", assigned: 191, resolved: 170, sla: "86%", open: 21, nodalOfficer: "Neha Sharma", zone: "Central & South" },
  { id: 5, name: "Environment", assigned: 124, resolved: 115, sla: "92%", open: 9, nodalOfficer: "Arjun Kapoor", zone: "Parks & Green Belts" },
  { id: 6, name: "Public Safety", assigned: 96, resolved: 84, sla: "90%", open: 12, nodalOfficer: "Priya Nair", zone: "Citywide" },
  { id: 7, name: "Drainage", assigned: 200, resolved: 175, sla: "88%", open: 25, nodalOfficer: "Sanjay Yadav", zone: "Low-lying Wards" }
];

export const mockAdminGovernance = {
  assessmentStates: [
    { code: "FULLY_RESOLVED", label: "Confirmed resolution with photographic evidence", color: "#10B981" },
    { code: "PARTIALLY_RESOLVED", label: "Temporary fix applied, permanent repair pending", color: "#06B6D4" },
    { code: "NOT_RESOLVED", label: "False completion claim or zero field progress", color: "#EF4444" },
    { code: "HUMAN_REVIEW", label: "Flagged for manual governance audit", color: "#8B5CF6" }
  ],
  queue: [
    {
      id: "CT-INC-0024",
      title: "Conflicting jurisdiction",
      category: "Ownership conflict",
      desc: "Asset ownership and maintenance responsibility records conflict between PWD and Lucknow Municipal Corporation.",
      reason: "Asset ownership and maintenance responsibility records conflict.",
      status: "Review Required",
      date: "12 Sept 2024"
    },
    {
      id: "CT-INC-0018",
      title: "Missing location",
      category: "Geospatial mismatch",
      desc: "The incident cannot be reliably placed in a service ward boundary.",
      reason: "GPS lock degraded due to overhead structure; address text ambiguous.",
      status: "Review Required",
      date: "11 Sept 2024"
    },
    {
      id: "CT-INC-0015",
      title: "Conflicting resolution evidence",
      category: "Evidence conflict",
      desc: "Submitted completion photo fails AI match with reported scene timestamp.",
      reason: "Submitted evidence does not consistently support closure.",
      status: "Evidence Disputed",
      date: "10 Sept 2024"
    },
    {
      id: "CT-INC-0009",
      title: "Insufficient evidence",
      category: "Low confidence",
      desc: "Available photo, timestamp, and location telemetry is inadequate for automated closure.",
      reason: "Available photo/time/location evidence is not enough for a decision.",
      status: "Review Required",
      date: "09 Sept 2024"
    }
  ]
};

export const mockAdminSettings = {
  account: {
    name: "Admin User",
    role: "System Administrator",
    authMethod: "Government SSO (e-Pramaan)",
    sessionTimeout: "30 minutes"
  },
  notifications: {
    criticalIncidents: true,
    slaBreachAlerts: true,
    dailyDigest: true,
    digestTime: "10:00 AM"
  },
  preferences: {
    defaultLocation: "Lucknow · All Wards",
    dataRefresh: "Every 5 minutes",
    timezone: "Asia/Kolkata (IST)"
  },
  governance: {
    auditRetention: "7 years",
    evidenceVerificationRequired: true,
    adminActionLogging: "All actions logged"
  }
};

