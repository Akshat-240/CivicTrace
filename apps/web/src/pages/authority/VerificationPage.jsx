import React, { useState, useEffect } from "react";
import PageHeader from "../../components/layout/PageHeader";
import Modal from "../../components/common/Modal";
import { Loader2, CheckCircle2, AlertTriangle, ClipboardList } from "lucide-react";
import {
  getIncidents,
  getIncident,
  getIncidentEvidence,
  submitResolutionEvidence,
  verifyResolution,
  humanVerifyResolution,
  closeIncident,
} from "../../services/api";
import "./VerificationPage.css";

// Real VerificationResult enum values from backend.
const GROUND_TRUTH_OPTIONS = [
  { key: "FULLY_RESOLVED",       label: "FULLY_RESOLVED",       colorClass: "ct-gt-green"  },
  { key: "PARTIALLY_RESOLVED",   label: "PARTIALLY_RESOLVED",   colorClass: "ct-gt-orange" },
  { key: "UNRESOLVED",           label: "UNRESOLVED",           colorClass: "ct-gt-red"    },
  { key: "INSUFFICIENT_EVIDENCE", label: "INSUFFICIENT_EVIDENCE", colorClass: "ct-gt-grey"  },
];

const VerificationPage = () => {
  const [allIncidents, setAllIncidents]     = useState([]);
  const [loading, setLoading]               = useState(true);
  const [currentIndex, setCurrentIndex]     = useState(0);
  const [banner, setBanner]                 = useState(null); // { text, ok }
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);

  // Resolution submission form
  const [resolutionDesc, setResolutionDesc] = useState("");
  const [submitting, setSubmitting]         = useState(false);

  // Auto-evaluation result (stage 2)
  const [autoResult, setAutoResult]         = useState(null); // null | { result, explanation, confidence }

  // Human decision (stage 3)
  const [selectedDecision, setSelectedDecision] = useState("FULLY_RESOLVED");
  const [decisionExplanation, setDecisionExplanation] = useState("");
  const [savingDecision, setSavingDecision] = useState(false);

  // Evidence list for current incident
  const [evidenceList, setEvidenceList]     = useState([]);

  const MOCK_AUTHORITY_ID = "61c6d93e-889d-42fc-b6b9-b167ce631d47";

  useEffect(() => {
    fetchPending();
  }, []);

  async function fetchPending() {
    try {
      setLoading(true);
      const res = await getIncidents(0, 100);
      const all = res?.data || [];
      const mine = all.filter((inc) => inc.authority?.id === MOCK_AUTHORITY_ID);
      // Show incidents that are ACTIVE or UNDER_REVIEW or RESOLVED (for closure)
      const candidates = mine.filter(
        (inc) => !["closed", "draft", "invalid"].includes(inc.status?.toLowerCase())
      );
      setAllIncidents(candidates);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const currentInc = allIncidents[currentIndex] || null;

  async function loadEvidenceForCurrent(incId) {
    try {
      const evList = await getIncidentEvidence(incId);
      setEvidenceList(evList || []);
    } catch {
      setEvidenceList([]);
    }
  }

  useEffect(() => {
    if (currentInc) {
      loadEvidenceForCurrent(currentInc.id);
      setAutoResult(currentInc.verification?.result ? currentInc.verification : null);
      setResolutionDesc("");
      setDecisionExplanation("");
    }
  }, [currentIndex, allIncidents]);

  function showBanner(text, ok = true) {
    setBanner({ text, ok });
    setTimeout(() => setBanner(null), 4000);
  }

  // Stage 1: Submit resolution evidence (ACTIVE -> UNDER_REVIEW)
  async function handleSubmitResolution() {
    if (!currentInc || !resolutionDesc.trim()) return;
    setSubmitting(true);
    try {
      await submitResolutionEvidence(currentInc.id, {
        description: resolutionDesc.trim(),
        evidence_type: "text",
      });
      showBanner(`Resolution evidence submitted. Incident is now UNDER_REVIEW.`);
      setResolutionDesc("");
      // Refresh incident list
      await fetchPending();
    } catch (err) {
      showBanner(`Failed to submit resolution: ${err.message}`, false);
    } finally {
      setSubmitting(false);
    }
  }

  // Stage 2: Run automatic evaluation
  async function handleAutoEvaluate() {
    if (!currentInc) return;
    setSubmitting(true);
    try {
      const rec = await verifyResolution(currentInc.id);
      setAutoResult(rec);
      showBanner(
        `Automatic evaluation: ${rec.result} (confidence ${Math.round((rec.confidence || 0) * 100)}%)`
      );
    } catch (err) {
      showBanner(`Auto-evaluation failed: ${err.message}`, false);
    } finally {
      setSubmitting(false);
    }
  }

  // Stage 3: Human decision
  async function handleSaveDecision() {
    if (!currentInc) return;
    setSavingDecision(true);
    try {
      const rec = await humanVerifyResolution(currentInc.id, {
        result: selectedDecision,
        explanation: decisionExplanation.trim() || undefined,
        // demo-authority-reviewer is applied server-side when verified_by is empty
        verified_by: "demo-authority-reviewer",
      });
      showBanner(
        `Decision saved: ${rec.result}. Incident status updated.`
      );
      setAutoResult(rec);
      await fetchPending();
    } catch (err) {
      showBanner(`Decision failed: ${err.message}`, false);
    } finally {
      setSavingDecision(false);
    }
  }

  // Stage 4: Close incident (RESOLVED -> CLOSED)
  async function handleCloseIncident() {
    if (!currentInc) return;
    setSubmitting(true);
    try {
      await closeIncident(currentInc.id);
      showBanner(`Incident closed successfully.`);
      await fetchPending();
      setCurrentIndex(0);
    } catch (err) {
      showBanner(`Close failed: ${err.message}`, false);
    } finally {
      setSubmitting(false);
    }
  }

  const incStatus = currentInc?.status?.toLowerCase();
  const isActive      = incStatus === "active";
  const isUnderReview = incStatus === "under_review";
  const isResolved    = incStatus === "resolved";

  const resolutionEvidence = evidenceList.filter((e) => e.is_verification_evidence);
  const citizenEvidence    = evidenceList.filter((e) => !e.is_verification_evidence);

  return (
    <div className="ct-verification-page">
      <PageHeader
        title="Incident Verification"
        subtitle="Resolution evidence → automatic evaluation → human decision → closure."
      />

      {banner && (
        <div className={`ct-save-banner${banner.ok ? "" : " error"}`}>
          {banner.ok ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          &nbsp;{banner.text}
        </div>
      )}

      {/* Top summary card */}
      <div className="ct-card ct-pending-card">
        <div className="ct-pending-left">
          <h2 className="ct-pending-title">Pending verification</h2>
          <p className="ct-pending-desc">
            {loading ? "Loading..." : `${allIncidents.length} cases require attention`}
          </p>
        </div>
        <div className="ct-pending-right">
          <span className="ct-evidence-badge">Evidence required</span>
        </div>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
          <Loader2 className="animate-spin" size={32} />
        </div>
      ) : allIncidents.length === 0 ? (
        <div style={{ textAlign: "center", padding: "4rem", background: "white", borderRadius: "8px" }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: "0 auto 1rem" }} />
          <h3>All caught up!</h3>
          <p style={{ color: "#6b7280" }}>No incidents currently await verification.</p>
        </div>
      ) : (
        <>
          {/* Incident navigation */}
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            {allIncidents.map((inc, idx) => (
              <button
                key={inc.id}
                onClick={() => setCurrentIndex(idx)}
                style={{
                  padding: "0.3rem 0.75rem",
                  borderRadius: "6px",
                  border: "1px solid #e5e7eb",
                  background: idx === currentIndex ? "#6366f1" : "white",
                  color: idx === currentIndex ? "white" : "#374151",
                  cursor: "pointer",
                  fontSize: "0.8rem",
                }}
              >
                {inc.reference_number || inc.id.substring(0, 8).toUpperCase()}
                &nbsp;<span style={{ opacity: 0.7 }}>[{inc.status?.toUpperCase()}]</span>
              </button>
            ))}
          </div>

          <div className="ct-verification-grid">
            {/* Left: Evidence Review */}
            <div className="ct-card ct-evidence-card">
              <div className="ct-card-head">
                <h2 className="ct-card-title">
                  {currentInc?.reference_number} · {currentInc?.title || currentInc?.issue_type}
                </h2>
                <p className="ct-card-desc">
                  Status: <strong>{incStatus?.replace("_", " ").toUpperCase()}</strong>
                  {currentInc?.authority && ` · ${currentInc.authority.department || currentInc.authority.name}`}
                </p>
              </div>

              <div className="ct-photo-panels">
                <div className="ct-photo-box">
                  <div className="ct-photo-tag">CITIZEN EVIDENCE ({citizenEvidence.length})</div>
                  <div className="ct-photo-visual">
                    {citizenEvidence.length > 0 ? (
                      citizenEvidence.map((e) => (
                        <p key={e.id} style={{ fontSize: "0.8rem", color: "#374151", margin: "0.25rem 0" }}>
                          {e.description || `[${e.evidence_type}]`}
                        </p>
                      ))
                    ) : (
                      <div className="ct-photo-placeholder-text">No citizen evidence</div>
                    )}
                  </div>
                </div>

                <div className="ct-photo-box">
                  <div className="ct-photo-tag">RESOLUTION EVIDENCE ({resolutionEvidence.length})</div>
                  <div className="ct-photo-visual">
                    {resolutionEvidence.length > 0 ? (
                      resolutionEvidence.map((e) => (
                        <p key={e.id} style={{ fontSize: "0.8rem", color: "#374151", margin: "0.25rem 0" }}>
                          {e.description || `[${e.evidence_type}]`}
                        </p>
                      ))
                    ) : (
                      <div className="ct-photo-placeholder-text">No resolution evidence yet</div>
                    )}
                  </div>
                </div>
              </div>

              {/* Auto-evaluation result (if run) */}
              {autoResult && (
                <div className="ct-evidence-footer" style={{ flexDirection: "column", alignItems: "flex-start", gap: "0.25rem" }}>
                  <div className="ct-evidence-pills">
                    <span className="ct-ai-verified-pill">
                      AUTO EVAL · {autoResult.result?.replace(/_/g, " ")}
                    </span>
                    <span className="ct-partial-pill">
                      Confidence: {Math.round((autoResult.confidence || 0) * 100)}%
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      by: {autoResult.verified_by || "system"}
                    </span>
                  </div>
                  {autoResult.explanation && (
                    <p style={{ fontSize: "0.8rem", color: "#6b7280", margin: "0.25rem 0 0" }}>
                      {autoResult.explanation}
                    </p>
                  )}
                </div>
              )}

              <div style={{ padding: "0.75rem 1.5rem", borderTop: "1px solid #f3f4f6" }}>
                <button
                  type="button"
                  className="ct-btn-openevidence"
                  onClick={() => setIsEvidenceModalOpen(true)}
                >
                  Open evidence detail
                </button>
              </div>
            </div>

            {/* Right: Action Panel */}
            <div className="ct-card ct-groundtruth-card">
              <div className="ct-card-head">
                <h2 className="ct-card-title">Verification Actions</h2>
                <p className="ct-card-desc">Complete each stage in order</p>
              </div>

              {/* STAGE 1: Submit resolution evidence (only if ACTIVE) */}
              {isActive && (
                <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #f3f4f6" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem", color: "#374151" }}>
                    Stage 1 — Submit Resolution Evidence
                  </p>
                  <textarea
                    rows={3}
                    placeholder="Describe the resolution work performed..."
                    value={resolutionDesc}
                    onChange={(e) => setResolutionDesc(e.target.value)}
                    style={{
                      width: "100%", border: "1px solid #e5e7eb", borderRadius: "6px",
                      padding: "0.5rem", fontSize: "0.85rem", resize: "vertical",
                    }}
                  />
                  <button
                    type="button"
                    className="ct-btn-savedecision"
                    onClick={handleSubmitResolution}
                    disabled={submitting || resolutionDesc.trim().length < 10}
                    style={{ marginTop: "0.5rem", opacity: resolutionDesc.trim().length < 10 ? 0.5 : 1 }}
                  >
                    {submitting ? "Submitting..." : "Submit Resolution →"}
                  </button>
                </div>
              )}

              {/* STAGE 2: Auto-evaluate (only if UNDER_REVIEW) */}
              {isUnderReview && (
                <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #f3f4f6" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem", color: "#374151" }}>
                    Stage 2 — Run Automatic Evaluation
                  </p>
                  <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                    System evaluates resolution evidence against original severity.
                    Result is advisory — does not change incident status.
                  </p>
                  <button
                    type="button"
                    className="ct-btn-savedecision"
                    onClick={handleAutoEvaluate}
                    disabled={submitting}
                    style={{ background: "#6366f1" }}
                  >
                    {submitting ? "Evaluating..." : "Run Auto-Evaluation"}
                  </button>
                </div>
              )}

              {/* STAGE 3: Human decision (only if UNDER_REVIEW) */}
              {isUnderReview && (
                <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #f3f4f6" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem", color: "#374151" }}>
                    Stage 3 — Human Verification Decision
                  </p>
                  <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.75rem" }}>
                    Reviewer: <strong>demo-authority-reviewer</strong> (no real auth in MVP)
                  </p>

                  <div className="ct-groundtruth-list">
                    {GROUND_TRUTH_OPTIONS.map((opt) => (
                      <div
                        key={opt.key}
                        className={`ct-groundtruth-item ${opt.colorClass} ${selectedDecision === opt.key ? "selected" : ""}`}
                        onClick={() => setSelectedDecision(opt.key)}
                      >
                        {opt.label}
                      </div>
                    ))}
                  </div>

                  <textarea
                    rows={2}
                    placeholder="Optional explanation for decision..."
                    value={decisionExplanation}
                    onChange={(e) => setDecisionExplanation(e.target.value)}
                    style={{
                      width: "100%", border: "1px solid #e5e7eb", borderRadius: "6px",
                      padding: "0.5rem", fontSize: "0.85rem", resize: "vertical", marginTop: "0.75rem",
                    }}
                  />

                  <div className="ct-decision-action">
                    <button
                      type="button"
                      className="ct-btn-savedecision"
                      onClick={handleSaveDecision}
                      disabled={savingDecision}
                    >
                      {savingDecision ? "Saving..." : "Save Decision"}
                    </button>
                  </div>
                </div>
              )}

              {/* STAGE 4: Close incident (only if RESOLVED) */}
              {isResolved && (
                <div style={{ padding: "1rem 1.5rem" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem", color: "#10b981" }}>
                    Stage 4 — Close Incident
                  </p>
                  <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "0.75rem" }}>
                    Resolution has been verified as FULLY_RESOLVED. Closing is final.
                  </p>
                  <button
                    type="button"
                    className="ct-btn-savedecision"
                    onClick={handleCloseIncident}
                    disabled={submitting}
                    style={{ background: "#10b981" }}
                  >
                    {submitting ? "Closing..." : "Close Incident"}
                  </button>
                </div>
              )}

              {/* Closed state message */}
              {incStatus === "closed" && (
                <div style={{ padding: "1.5rem", textAlign: "center" }}>
                  <CheckCircle2 size={32} color="#10b981" style={{ margin: "0 auto 0.5rem" }} />
                  <p style={{ color: "#374151", fontWeight: 600 }}>Incident Closed</p>
                  <p style={{ color: "#6b7280", fontSize: "0.85rem" }}>No further action required.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Evidence Inspection Modal */}
      {currentInc && (
        <Modal
          isOpen={isEvidenceModalOpen}
          onClose={() => setIsEvidenceModalOpen(false)}
          title={`Evidence: ${currentInc.reference_number}`}
        >
          <div className="ct-modal-evidence-detail">
            <div className="ct-evidence-meta-row">
              <div><strong>Location:</strong> {currentInc.location?.address_raw || "Unknown"}</div>
              <div><strong>Authority:</strong> {currentInc.authority?.name || "N/A"}</div>
              <div><strong>Status:</strong> {incStatus?.replace("_", " ").toUpperCase()}</div>
            </div>

            <div className="ct-modal-photo-preview">
              <div className="ct-modal-photo-col">
                <h4>Citizen Evidence ({citizenEvidence.length} items)</h4>
                {citizenEvidence.map((e) => (
                  <div key={e.id} className="ct-modal-photo-frame">
                    <span className="ct-frame-tag">{e.evidence_type?.toUpperCase()}</span>
                    <p style={{ fontSize: "0.85rem", color: "#374151" }}>{e.description || "(no description)"}</p>
                    <p className="ct-frame-meta">Submitted: {new Date(e.created_at).toLocaleString()}</p>
                  </div>
                ))}
                {citizenEvidence.length === 0 && <p style={{ color: "#6b7280" }}>None</p>}
              </div>
              <div className="ct-modal-photo-col">
                <h4>Resolution Evidence ({resolutionEvidence.length} items)</h4>
                {resolutionEvidence.map((e) => (
                  <div key={e.id} className="ct-modal-photo-frame">
                    <span className="ct-frame-tag">{e.evidence_type?.toUpperCase()}</span>
                    <p style={{ fontSize: "0.85rem", color: "#374151" }}>{e.description || "(no description)"}</p>
                    <p className="ct-frame-meta">Submitted: {new Date(e.created_at).toLocaleString()}</p>
                  </div>
                ))}
                {resolutionEvidence.length === 0 && (
                  <p style={{ color: "#6b7280" }}>No resolution evidence submitted yet.</p>
                )}
              </div>
            </div>

            {autoResult && (
              <div style={{ marginTop: "1rem", padding: "0.75rem", background: "#f9fafb", borderRadius: "6px" }}>
                <strong style={{ fontSize: "0.85rem" }}>Latest Evaluation:</strong>
                <p style={{ fontSize: "0.85rem", color: "#374151", marginTop: "0.25rem" }}>
                  Result: {autoResult.result} · Confidence: {Math.round((autoResult.confidence || 0) * 100)}%
                  · By: {autoResult.verified_by || "system"}
                </p>
                <p style={{ fontSize: "0.8rem", color: "#6b7280" }}>{autoResult.explanation}</p>
              </div>
            )}

            <div className="ct-modal-actions">
              <button type="button" className="btn btn-outline" onClick={() => setIsEvidenceModalOpen(false)}>
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default VerificationPage;
