import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Road, 
  Trash2, 
  Droplet, 
  Waves, 
  Lightbulb, 
  Zap, 
  Mic, 
  ArrowRight, 
  Check, 
  UploadCloud, 
  MapPin, 
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  X,
  ShieldAlert,
  Image as ImageIcon,
  Square,
  Globe,
  FileText
} from 'lucide-react';
import { createIncident, uploadIncidentEvidence, analyzeEvidence, transcribeSpeech } from '../../services/api';
import './CitizenReportPage.css';

function encodeWAV(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (view, offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  // RIFF container
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, 'WAVE');

  // fmt chunk (Linear PCM, 1 channel mono, 16000 Hz, 16-bit)
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);

  // data chunk
  writeString(view, 36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([view], { type: 'audio/wav' });
}

export default function CitizenReportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const audioStreamRef = useRef(null);
  const pcmChunksRef = useRef([]);
  const scriptProcessorRef = useRef(null);
  const timerRef = useRef(null);

  const [currentStep, setCurrentStep] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState('Road');
  const [description, setDescription] = useState('');

  // Voice recording state: IDLE -> RECORDING -> TRANSCRIBING -> READY / TRANSCRIPTION_ERROR
  const [speechState, setSpeechState] = useState('IDLE');
  const [speechLanguage, setSpeechLanguage] = useState('en-US');
  const [speechError, setSpeechError] = useState(null);
  const [recordingSeconds, setRecordingSeconds] = useState(0);

  // File upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Submission & AI lifecycle states
  // Lifecycle: IDLE -> UPLOADING -> UPLOADED -> ANALYZING -> ANALYZED / AI_ERROR
  const [submittedId, setSubmittedId] = useState(null);
  const [realId, setRealId] = useState(null);
  const [uploadedEvidenceId, setUploadedEvidenceId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [aiLifecycleState, setAiLifecycleState] = useState('IDLE');
  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState(null);

  const categories = [
    { name: 'Road', icon: <Road size={20} />, label: 'Pothole, broken asphalt, road caving' },
    { name: 'Garbage', icon: <Trash2 size={20} />, label: 'Overflowing bins, open dumping' },
    { name: 'Water', icon: <Droplet size={20} />, label: 'Pipe burst, water contamination' },
    { name: 'Drainage', icon: <Waves size={20} />, label: 'Blocked storm drain, sewer backflow' },
    { name: 'Streetlight', icon: <Lightbulb size={20} />, label: 'Light not working, flickering, dark spot' },
    { name: 'Electrical', icon: <Zap size={20} />, label: 'Exposed wiring, spark hazard, transformer' },
  ];

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (scriptProcessorRef.current) scriptProcessorRef.current.disconnect();
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
      if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  const handleStartRecording = async () => {
    try {
      setSpeechError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      pcmChunksRef.current = [];
      audioChunksRef.current = [];

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        const audioCtx = new AudioContextClass({ sampleRate: 16000 });
        audioContextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);
        scriptProcessorRef.current = processor;

        processor.onaudioprocess = (e) => {
          const input = e.inputBuffer.getChannelData(0);
          pcmChunksRef.current.push(new Float32Array(input));
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);
      } else {
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        mediaRecorder.start();
      }

      setSpeechState('RECORDING');
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds(sec => sec + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone error:', err);
      setSpeechError('Microphone access denied or not supported in browser. You can type your briefing.');
      setSpeechState('TRANSCRIPTION_ERROR');
    }
  };

  const handleStopRecording = async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop());
      audioStreamRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }

    let audioBlob = null;
    if (pcmChunksRef.current.length > 0) {
      const totalLen = pcmChunksRef.current.reduce((acc, curr) => acc + curr.length, 0);
      const merged = new Float32Array(totalLen);
      let offset = 0;
      for (const chunk of pcmChunksRef.current) {
        merged.set(chunk, offset);
        offset += chunk.length;
      }
      pcmChunksRef.current = [];
      audioBlob = encodeWAV(merged, 16000);
    } else if (audioChunksRef.current.length > 0) {
      audioBlob = new Blob(audioChunksRef.current, {
        type: mediaRecorderRef.current?.mimeType || 'audio/webm'
      });
      audioChunksRef.current = [];
    }

    if (!audioBlob || audioBlob.size === 0) {
      setSpeechState('IDLE');
      return;
    }

    setSpeechState('TRANSCRIBING');
    try {
      const res = await transcribeSpeech(audioBlob, speechLanguage);
      if (res && res.text) {
        setDescription(prev => {
          const clean = (prev || '').trim();
          return clean ? `${clean} ${res.text}` : res.text;
        });
        setSpeechState('READY');
      } else {
        setSpeechState('IDLE');
      }
    } catch (err) {
      console.error('Speech transcription error:', err);
      setSpeechError(err.message || 'Voice transcription service unavailable. You can type manually.');
      setSpeechState('TRANSCRIPTION_ERROR');
    }
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file (JPEG, PNG, WebP).');
      return;
    }
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleRemoveFile = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const runAIAnalysis = async (incidentId, evidenceId) => {
    try {
      setAiLifecycleState('ANALYZING');
      setAiError(null);
      const result = await analyzeEvidence(incidentId, evidenceId);
      setAiResult(result);
      setAiLifecycleState('ANALYZED');
    } catch (err) {
      console.error('AI analysis error:', err);
      setAiError(err.message || 'AI perception analysis encountered an issue.');
      setAiLifecycleState('AI_ERROR');
    }
  };

  const handleRetryAI = async () => {
    if (realId && uploadedEvidenceId) {
      await runAIAnalysis(realId, uploadedEvidenceId);
    }
  };

  const handleNextStep = async (e) => {
    e.preventDefault();
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      // Step 4: Complete submission
      setIsSubmitting(true);
      setSubmitError(null);
      
      const issueTypeMap = {
        'Road': 'road_damage',
        'Garbage': 'illegal_dumping',
        'Water': 'water_leak',
        'Drainage': 'sewage_overflow',
        'Streetlight': 'broken_streetlight',
        'Electrical': 'other'
      };
      
      const payload = {
        title: selectedCategory + ' Issue',
        description: description || 'Citizen reported issue regarding ' + selectedCategory.toLowerCase() + '.',
        issue_type: issueTypeMap[selectedCategory] || 'other',
        location: {
          latitude: 26.8467,
          longitude: 80.9462,
          address_raw: "MG Road, Near Hazratganj Crossing"
        }
      };

      try {
        // 1. Create Incident
        const incidentResponse = await createIncident(payload);
        const incId = incidentResponse.id;
        setSubmittedId(incidentResponse.reference_number || incId);
        setRealId(incId);

        // 2. If photo is attached, upload evidence and trigger AI perception
        if (selectedFile) {
          setAiLifecycleState('UPLOADING');
          const formData = new FormData();
          formData.append('file', selectedFile);
          formData.append('description', description || `${selectedCategory} issue photo evidence`);
          formData.append('latitude', '26.8467');
          formData.append('longitude', '80.9462');
          formData.append('address_raw', 'MG Road, Near Hazratganj Crossing');
          formData.append('evidence_type', 'image');

          const uploadResponse = await uploadIncidentEvidence(incId, formData);
          setUploadedEvidenceId(uploadResponse.id);
          setAiLifecycleState('UPLOADED');

          // 3. Trigger AI analysis on the uploaded evidence item
          await runAIAnalysis(incId, uploadResponse.id);
        } else if (incidentResponse.primary_evidence_id) {
          // If text-only, analyze the initial atomic evidence created during incident submission
          setUploadedEvidenceId(incidentResponse.primary_evidence_id);
          await runAIAnalysis(incId, incidentResponse.primary_evidence_id);
        }
      } catch (err) {
        console.error('Failed to submit incident:', err);
        setSubmitError('Failed to submit incident. Please check your connection and try again.');
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="citizen-report-container">
      {/* 4-Step Stepper */}
      <div className="citizen-stepper-bar">
        {[
          { num: 1, label: '1 Issue' },
          { num: 2, label: '2 Evidence' },
          { num: 3, label: '3 Location' },
          { num: 4, label: '4 Review' }
        ].map((s) => (
          <div 
            key={s.num}
            className={`stepper-pill ${currentStep === s.num ? 'active' : currentStep > s.num ? 'completed' : ''}`}
            onClick={() => setCurrentStep(s.num)}
          >
            {s.label}
          </div>
        ))}
      </div>

      {submittedId ? (
        /* Submission Success View with Live Real AI Results */
        <div className="report-success-card">
          <div className="success-icon-wrapper">
            <CheckCircle2 size={48} className="success-check-icon" />
          </div>
          <h2 className="success-title">Report Filed Successfully!</h2>
          <p className="success-subtitle">
            Your complaint has been assigned incident ID <strong className="id-highlight">{submittedId}</strong> and routed to the municipal triage engine.
          </p>

          {/* AI Lifecycle Display */}
          {aiLifecycleState === 'ANALYZING' && (
            <div className="ai-analyzing-box">
              <Loader2 size={20} className="animate-spin" />
              <span>AI perception engine is analyzing evidence in real time...</span>
            </div>
          )}

          {aiLifecycleState === 'ANALYZED' && aiResult && (
            <div className="ai-perception-card">
              <div className="ai-card-header">
                <div className="ai-card-title-group">
                  <Sparkles size={18} className="ai-sparkle-icon" />
                  <h3 className="ai-card-title">AI Multi-Modal Perception</h3>
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <span className="ai-provider-badge">
                    {aiResult.extracted_attributes?.provider === 'azure_computer_vision'
                      ? 'Azure Computer Vision'
                      : 'Gemini AI'}
                  </span>
                  {aiResult.language_perception && aiResult.language_perception.status === 'success' && (
                    <span className="ai-provider-badge language-badge">
                      Azure AI Language
                    </span>
                  )}
                </div>
              </div>

              <div className="ai-grid">
                {/* 1. Visual Findings */}
                <div className="ai-field">
                  <span className="ai-field-label">Detected Visual Category</span>
                  <span className="ai-field-value highlight">
                    {aiResult.civic_issue_category
                      ? aiResult.civic_issue_category.toUpperCase().replace(/_/g, ' ')
                      : 'Uncertain / General'}
                  </span>
                </div>

                <div className="ai-field">
                  <span className="ai-field-label">Perception Confidence</span>
                  <span className="ai-field-value">
                    {Math.round((aiResult.confidence || 0) * 100)}%
                  </span>
                </div>

                <div className="ai-field">
                  <span className="ai-field-label">Assessed Severity</span>
                  <span className={`ai-field-value severity-${(aiResult.severity_assessment || 'low').toLowerCase()}`}>
                    {aiResult.severity_assessment ? aiResult.severity_assessment.toUpperCase() : 'None / Low'}
                  </span>
                </div>

                <div className="ai-field">
                  <span className="ai-field-label">Perception Clarity</span>
                  <span className="ai-field-value">
                    {aiResult.ambiguity_flag ? 'Ambiguous / Needs Review' : 'High Clarity'}
                  </span>
                </div>

                {/* Safety Warning */}
                {aiResult.safety_risk_detected && (
                  <div className="ai-field full-width">
                    <span className="ai-field-label">Safety Risk Warning</span>
                    <span className="ai-hazard-pill">
                      <ShieldAlert size={14} />
                      Potential Physical Safety Hazard Detected
                    </span>
                  </div>
                )}

                {/* Conflict / Ambiguity Alert */}
                {aiResult.ambiguity_flag && aiResult.ambiguity_reason && (
                  <div className="ai-field full-width">
                    <div className="ai-conflict-banner">
                      <AlertTriangle size={16} color="#D97706" />
                      <span>{aiResult.ambiguity_reason}</span>
                    </div>
                  </div>
                )}

                {/* 2. Visual Observation */}
                <div className="ai-field full-width">
                  <span className="ai-field-label">Visual Finding</span>
                  <span className="ai-field-value">{aiResult.explanation}</span>
                </div>

                {/* 3. Written Briefing & Language Perception */}
                {description && (
                  <div className="ai-field full-width">
                    <span className="ai-field-label">Citizen Problem Briefing</span>
                    <span className="ai-field-value briefing-text">"{description.trim()}"</span>
                  </div>
                )}

                {aiResult.language_perception && aiResult.language_perception.status === 'success' && (
                  <div className="ai-field full-width">
                    <span className="ai-field-label">Language Analysis (Azure AI Language)</span>
                    <div className="language-tags-row">
                      {aiResult.language_perception.detected_category && (
                        <span className="lang-tag category">
                          Category: {aiResult.language_perception.detected_category.replace(/_/g, ' ')}
                        </span>
                      )}
                      {(aiResult.language_perception.issue_terms || []).map((term, idx) => (
                        <span key={idx} className="lang-tag term">
                          #{term}
                        </span>
                      ))}
                      {(aiResult.language_perception.impact_phrases || []).map((phrase, idx) => (
                        <span key={idx} className="lang-tag impact">
                          {phrase}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 4. Combined Interpretation */}
                <div className="ai-field full-width combined-field">
                  <span className="ai-field-label">Combined AI Interpretation</span>
                  <p className="combined-interpretation-text">
                    {aiResult.combined_interpretation || aiResult.explanation}
                  </p>
                </div>
              </div>
            </div>
          )}

          {aiLifecycleState === 'AI_ERROR' && (
            <div className="ai-error-box">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={20} color="#DC2626" />
                <p className="ai-error-text">
                  AI analysis could not complete: {aiError}. Your evidence and incident report are safely preserved.
                </p>
              </div>
              <button
                type="button"
                className="btn-retry-ai"
                onClick={handleRetryAI}
              >
                <RefreshCw size={14} />
                <span>Retry AI</span>
              </button>
            </div>
          )}

          <div className="success-actions">
            <button 
              className="btn-track-submitted"
              onClick={() => navigate(`/citizen/track?id=${realId || submittedId}`)}
            >
              Track Report ({submittedId})
            </button>
            <button 
              className="btn-back-dashboard"
              onClick={() => navigate('/citizen/dashboard')}
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      ) : (
        /* Form & Explainer Grid */
        <div className="citizen-report-grid">
          {/* Main Form Panel */}
          <div className="citizen-report-form-panel">
            {submitError && (
              <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={16} />
                <span style={{ fontSize: '0.9rem' }}>{submitError}</span>
              </div>
            )}
            
            {currentStep === 1 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">What happened?</h2>
                  <p className="report-step-subtitle">Choose the closest category so we can understand your report.</p>
                </div>

                {/* Categories 3x2 Grid */}
                <div className="categories-grid">
                  {categories.map((cat) => (
                    <div 
                      key={cat.name}
                      className={`category-select-card ${selectedCategory === cat.name ? 'selected' : ''}`}
                      onClick={() => setSelectedCategory(cat.name)}
                    >
                      <div className="category-icon-title">
                        <span className="cat-icon">{cat.icon}</span>
                        <span className="cat-name">{cat.name}</span>
                      </div>
                      <span className="cat-select-indicator">
                        {selectedCategory === cat.name ? 'Selected' : 'Select'}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Description Textarea with Voice Recording & Language Selector */}
                <div className="report-desc-box">
                  <div className="desc-header-row">
                    <label className="desc-label">Problem Briefing (Written or Spoken)</label>
                    <div className="speech-lang-selector">
                      <Globe size={13} />
                      <select
                        value={speechLanguage}
                        onChange={(e) => setSpeechLanguage(e.target.value)}
                        className="speech-lang-dropdown"
                        disabled={speechState === 'RECORDING'}
                      >
                        <option value="en-US">English (en-US)</option>
                        <option value="hi-IN">Hindi (hi-IN / लखनऊ)</option>
                      </select>
                    </div>
                  </div>

                  <div className="desc-textarea-wrapper">
                    <textarea
                      className="desc-textarea"
                      placeholder="Describe the issue (e.g. Large pothole outside the school, fills with water whenever it rains)..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={3}
                    />

                    {speechState === 'IDLE' || speechState === 'READY' || speechState === 'TRANSCRIPTION_ERROR' ? (
                      <button
                        type="button"
                        className="mic-btn"
                        onClick={handleStartRecording}
                        title="Speak your briefing (Azure Speech-to-Text)"
                      >
                        <Mic size={18} />
                      </button>
                    ) : speechState === 'RECORDING' ? (
                      <button
                        type="button"
                        className="mic-btn recording"
                        onClick={handleStopRecording}
                        title="Stop recording"
                      >
                        <Square size={16} />
                      </button>
                    ) : (
                      <div className="mic-btn transcribing">
                        <Loader2 size={16} className="animate-spin" />
                      </div>
                    )}
                  </div>

                  {/* Voice recording active state feedback */}
                  {speechState === 'RECORDING' && (
                    <div className="voice-recording-banner">
                      <div className="recording-pulse-dot" />
                      <span>Recording voice briefing ({recordingSeconds}s)... Speak clearly.</span>
                      <button
                        type="button"
                        className="btn-stop-voice"
                        onClick={handleStopRecording}
                      >
                        Stop & Transcribe
                      </button>
                    </div>
                  )}

                  {speechState === 'TRANSCRIBING' && (
                    <div className="voice-transcribing-banner">
                      <Loader2 size={14} className="animate-spin" />
                      <span>Converting speech to text via Azure AI Speech...</span>
                    </div>
                  )}

                  {speechState === 'TRANSCRIPTION_ERROR' && speechError && (
                    <div className="voice-error-banner">
                      <AlertTriangle size={14} />
                      <span>{speechError}</span>
                      <button type="button" className="btn-dismiss-err" onClick={() => setSpeechError(null)}>×</button>
                    </div>
                  )}

                  <span className="desc-hint">
                    Type your description or press the microphone to speak. The final editable briefing will be analyzed by Azure AI Language.
                  </span>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Continue</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 2 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Upload Evidence</h2>
                  <p className="report-step-subtitle">Photographs allow automated AI verification and rapid authority dispatch.</p>
                </div>

                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileChange}
                />

                {selectedFile ? (
                  <div className="real-photo-preview">
                    {previewUrl ? (
                      <img src={previewUrl} alt="Evidence preview" className="photo-preview-thumbnail" />
                    ) : (
                      <ImageIcon size={32} className="photo-preview-thumbnail" />
                    )}
                    <div className="photo-preview-info">
                      <span className="photo-preview-name">{selectedFile.name}</span>
                      <span className="photo-preview-meta">
                        {(selectedFile.size / 1024).toFixed(1)} KB · {selectedFile.type || 'image'}
                      </span>
                      <span className="photo-preview-badge">
                        <Check size={12} />
                        Ready for AI Perception
                      </span>
                    </div>
                    <button
                      type="button"
                      className="btn-remove-photo"
                      onClick={handleRemoveFile}
                      title="Remove photo"
                    >
                      <X size={14} />
                      <span>Remove</span>
                    </button>
                  </div>
                ) : (
                  <div
                    className={`evidence-upload-zone ${isDragging ? 'dragging' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <UploadCloud size={36} className="upload-cloud-icon" />
                    <p className="upload-zone-prompt">Drag & drop photo here or <span>Browse Files</span></p>
                    <span className="upload-zone-hint">Supports JPEG, PNG, WEBP up to 15MB. Real photographs will be processed by Azure Computer Vision.</span>
                  </div>
                )}

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(1)}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Continue to Location</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 3 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Confirm Location</h2>
                  <p className="report-step-subtitle">Exact location ensures your complaint reaches the correct ward nodal officer.</p>
                </div>

                <div className="location-confirm-box">
                  <div className="location-pin-header">
                    <MapPin size={20} className="loc-marker-icon" />
                    <div>
                      <h4 className="loc-addr-title">MG Road, Near Hazratganj Crossing</h4>
                      <p className="loc-addr-meta">Ward 12 · Zone 1 · Lucknow (Lat: 26.8467, Long: 80.9462)</p>
                    </div>
                  </div>

                  <div className="simulated-map-box">
                    <div className="map-circle-ping"></div>
                    <span className="map-ping-label">Incident GPS Lock Acquired</span>
                  </div>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(2)}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Review & Submit</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 4 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Review & Submit</h2>
                  <p className="report-step-subtitle">Inspect the normalized report details before official dispatch.</p>
                </div>

                <div className="review-summary-list">
                  <div className="review-row">
                    <span className="review-key">Category</span>
                    <span className="review-val category-tag">{selectedCategory}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Description</span>
                    <span className="review-val">{description || 'Citizen reported issue regarding ' + selectedCategory.toLowerCase() + '.'}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Attached Evidence</span>
                    <span className="review-val">
                      {selectedFile
                        ? `${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`
                        : 'Text Description Only'}
                    </span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Location</span>
                    <span className="review-val">MG Road, Near Hazratganj Crossing · Ward 12</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Responsible Department</span>
                    <span className="review-val">Lucknow Municipal Corporation · Roads Division</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Estimated SLA Target</span>
                    <span className="review-val highlight">Within 24 Hours</span>
                  </div>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(3)}
                    disabled={isSubmitting}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-submit-final"
                    onClick={handleNextStep}
                    disabled={isSubmitting}
                    style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        <span>
                          {aiLifecycleState === 'UPLOADING'
                            ? 'Uploading Evidence...'
                            : aiLifecycleState === 'ANALYZING'
                            ? 'AI Analyzing...'
                            : 'Submitting Incident Report...'}
                        </span>
                      </>
                    ) : (
                      <>
                        <Check size={16} />
                        <span>Submit Incident Report</span>
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Side Card: What happens next? */}
          <div className="citizen-explainer-card">
            <h3 className="explainer-title">What happens next?</h3>

            <div className="explainer-steps-list">
              <div className="explainer-step-item">
                <div className="explainer-num-badge">1</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">AI structures your report</h4>
                  <p className="explainer-step-body">Visual & text perception normalizes features</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">2</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">Location is verified</h4>
                  <p className="explainer-step-body">GIS containment identifies jurisdiction</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">3</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">Duplicates are checked</h4>
                  <p className="explainer-step-body">Spatial & temporal fusion engine links reports</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">4</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">SLA clock started</h4>
                  <p className="explainer-step-body">Deterministic category rules apply</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
