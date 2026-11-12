/**
 * Industrial Safety AI Surveillance System
 * Phase 2: Video Surveillance, Live Monitoring & Alerts
 */

// Application State
const state = {
  currentView: 'dashboard',
  modelInfo: null,
  isModelReady: false,
  confThreshold: 0.15,

  // Image Detection State (Phase 1)
  selectedImageFile: null,
  annotatedImageUrl: null,
  isImageProcessing: false,

  // Video Detection State (Phase 2)
  selectedVideoFile: null,
  activeVideoJobId: null,
  videoPollingInterval: null,
  isVideoProcessing: false,
  annotatedVideoUrl: null,

  // Live Webcam Monitoring State (Phase 2)
  isLiveMonitoring: false,
  isLiveInferencePaused: false,
  webcamStream: null,
  liveInferenceInterval: null,
  liveFpsCounter: 0,
  liveLastFpsTime: Date.now(),
  liveViolationsTotal: 0,

  // Alerts & Incidents State
  unacknowledgedAlertsCount: 0,
  incidentsList: [],

  // Phase 3: Analytics State
  analyticsFilter: {
    range: '30d',
    startDate: '',
    endDate: '',
    category: 'ALL',
    severity: 'ALL',
    source: 'ALL'
  },
  charts: {
    violations: null,
    trends: null,
    severity: null,
    sources: null,
    dashTrends: null,
    dashViolations: null
  },

  // Phase 3: Incident History & Management State
  incidentHistoryFilter: {
    search: '',
    category: 'ALL',
    severity: 'ALL',
    source: 'ALL',
    status: 'ALL',
    startDate: '',
    endDate: '',
    page: 1,
    limit: 10,
    totalPages: 1,
    totalRecords: 0
  },
  activeIncidentForModal: null,

  // Phase 3: Reports State
  selectedReportFormat: 'pdf'
};

// ============================================================================
// DOM ELEMENTS
// ============================================================================
const elements = {
  // Topbar
  topModelStatus: document.getElementById('topModelStatus'),
  topModelIcon: document.getElementById('topModelIcon'),
  topModelLabel: document.getElementById('topModelLabel'),
  topAlertBell: document.getElementById('topAlertBell'),
  topAlertCount: document.getElementById('topAlertCount'),
  sidebarAlertBadge: document.getElementById('sidebarAlertBadge'),
  infoBtn: document.getElementById('infoBtn'),
  infoModal: document.getElementById('infoModal'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalOkBtn: document.getElementById('modalOkBtn'),
  profileDropdown: document.getElementById('profileDropdown'),
  profileMenu: document.getElementById('profileMenu'),
  sidebarToggle: document.getElementById('sidebarToggle'),
  sidebar: document.getElementById('sidebar'),

  // Image Detection (Phase 1)
  dropZone: document.getElementById('dropZone'),
  dropZonePrompt: document.getElementById('dropZonePrompt'),
  imageInput: document.getElementById('imageInput'),
  chooseImgBtn: document.getElementById('chooseImgBtn'),
  stagedPreview: document.getElementById('stagedPreview'),
  stagedThumb: document.getElementById('stagedThumb'),
  stagedName: document.getElementById('stagedName'),
  stagedSize: document.getElementById('stagedSize'),
  btnRemoveStaged: document.getElementById('btnRemoveStaged'),
  loadSampleBtn: document.getElementById('loadSampleBtn'),
  resultPlaceholder: document.getElementById('resultPlaceholder'),
  canvasWrapper: document.getElementById('canvasWrapper'),
  resultImage: document.getElementById('resultImage'),
  processingOverlay: document.getElementById('processingOverlay'),
  inferenceTimerBadge: document.getElementById('inferenceTimerBadge'),
  inferenceTimeVal: document.getElementById('inferenceTimeVal'),
  detectionTableBody: document.getElementById('detectionTableBody'),
  summaryTotalCount: document.getElementById('summaryTotalCount'),
  summaryUniqueClasses: document.getElementById('summaryUniqueClasses'),
  summaryPeakConf: document.getElementById('summaryPeakConf'),
  btnRunDetection: document.getElementById('btnRunDetection'),
  btnClearAll: document.getElementById('btnClearAll'),
  btnDownloadResult: document.getElementById('btnDownloadResult'),

  // Video Detection (Phase 2 - Matching Reference Design)
  videoDropZone: document.getElementById('videoDropZone'),
  videoFileInput: document.getElementById('videoFileInput'),
  chooseVideoBtn: document.getElementById('chooseVideoBtn'),
  stagedVideoPillCard: document.getElementById('stagedVideoPillCard'),
  stagedVideoThumbImg: document.getElementById('stagedVideoThumbImg'),
  stagedVideoName: document.getElementById('stagedVideoName'),
  stagedVideoMeta: document.getElementById('stagedVideoMeta'),
  btnRemoveStagedVideo: document.getElementById('btnRemoveStagedVideo'),
  loadSampleVideoBtn: document.getElementById('loadSampleVideoBtn'),
  mainSurveillanceVideo: document.getElementById('mainSurveillanceVideo'),
  videoCanvasOverlay: document.getElementById('videoCanvasOverlay'),
  videoProcessingOverlay: document.getElementById('videoProcessingOverlay'),
  videoProcessingText: document.getElementById('videoProcessingText'),
  overlayProgressFill: document.getElementById('overlayProgressFill'),
  videoAnalysisStatusPill: document.getElementById('videoAnalysisStatusPill'),
  ctrlPlayPause: document.getElementById('ctrlPlayPause'),
  ctrlStop: document.getElementById('ctrlStop'),
  videoTimer: document.getElementById('videoTimer'),
  videoScrubber: document.getElementById('videoScrubber'),
  scrubberFill: document.getElementById('scrubberFill'),
  ctrlVolume: document.getElementById('ctrlVolume'),
  ctrlFullscreen: document.getElementById('ctrlFullscreen'),
  btnAnalyzeVideo: document.getElementById('btnAnalyzeVideo'),
  btnDownloadVideoResult: document.getElementById('btnDownloadVideoResult'),
  btnClearVideo: document.getElementById('btnClearVideo'),
  analysisCompletedBadge: document.getElementById('analysisCompletedBadge'),
  timelineTableBody: document.getElementById('timelineTableBody'),

  // Summary Metrics
  metricVideosAnalyzed: document.getElementById('metricVideosAnalyzed'),
  metricVideoTotalDetections: document.getElementById('metricVideoTotalDetections'),
  metricVideoUniqueObjects: document.getElementById('metricVideoUniqueObjects'),
  metricVideoViolations: document.getElementById('metricVideoViolations'),
  metricComplianceRate: document.getElementById('metricComplianceRate'),
  countHelmet: document.getElementById('countHelmet'),
  countVest: document.getElementById('countVest'),
  countGloves: document.getElementById('countGloves'),
  countGoggles: document.getElementById('countGoggles'),
  countBoots: document.getElementById('countBoots'),
  countViolations: document.getElementById('countViolations'),
  countHelmetFrames: document.getElementById('countHelmetFrames'),
  countVestFrames: document.getElementById('countVestFrames'),
  countGlovesFrames: document.getElementById('countGlovesFrames'),
  countGogglesFrames: document.getElementById('countGogglesFrames'),
  countBootsFrames: document.getElementById('countBootsFrames'),
  countViolationsFrames: document.getElementById('countViolationsFrames'),
  detailTotalFrames: document.getElementById('detailTotalFrames'),
  detailFramesProcessed: document.getElementById('detailFramesProcessed'),
  detailProcessingFps: document.getElementById('detailProcessingFps'),
  detailTotalDetections: document.getElementById('detailTotalDetections'),
  detailUniqueObjects: document.getElementById('detailUniqueObjects'),
  detailTotalViolations: document.getElementById('detailTotalViolations'),
  detailProcessingTime: document.getElementById('detailProcessingTime'),

  // Live Monitoring (Phase 2)
  webcamVideo: document.getElementById('webcamVideo'),
  webcamCanvasOverlay: document.getElementById('webcamCanvasOverlay'),
  offscreenCanvas: document.getElementById('offscreenCanvas'),
  liveOfflineOverlay: document.getElementById('liveOfflineOverlay'),
  liveIndicatorPill: document.getElementById('liveIndicatorPill'),
  liveCameraStatus: document.getElementById('liveCameraStatus'),
  liveFeedFps: document.getElementById('liveFeedFps'),
  liveCurrentDetections: document.getElementById('liveCurrentDetections'),
  liveViolationsCount: document.getElementById('liveViolationsCount'),
  btnStartCamera: document.getElementById('btnStartCamera'),
  btnStopCamera: document.getElementById('btnStopCamera'),
  btnPauseCameraStream: document.getElementById('btnPauseCameraStream'),
  liveLatestEvidenceContainer: document.getElementById('liveLatestEvidenceContainer'),
  liveAlertsScroll: document.getElementById('liveAlertsScroll'),
  btnClearLiveAlerts: document.getElementById('btnClearLiveAlerts'),

  // Alerts & Incidents Table
  incidentsMasterTableBody: document.getElementById('incidentsMasterTableBody'),
  alertStatTotal: document.getElementById('alertStatTotal'),
  alertStatCritical: document.getElementById('alertStatCritical'),
  alertStatHigh: document.getElementById('alertStatHigh'),
  alertStatUnack: document.getElementById('alertStatUnack'),
  filterSeverity: document.getElementById('filterSeverity'),
  filterStatus: document.getElementById('filterStatus'),
  btnRefreshAlerts: document.getElementById('btnRefreshAlerts'),

  // Evidence Modal
  evidenceModal: document.getElementById('evidenceModal'),
  evidenceModalCloseBtn: document.getElementById('evidenceModalCloseBtn'),
  evidenceModalImg: document.getElementById('evidenceModalImg'),
  evidenceModalMeta: document.getElementById('evidenceModalMeta'),
  evidenceDownloadBtn: document.getElementById('evidenceDownloadBtn'),

  // Model Info
  specModelName: document.getElementById('specModelName'),
  specModelPath: document.getElementById('specModelPath'),
  specArchitecture: document.getElementById('specArchitecture'),
  specDevice: document.getElementById('specDevice'),
  specStatus: document.getElementById('specStatus'),
  specsClassesTableBody: document.getElementById('specsClassesTableBody'),
  confSlider: document.getElementById('confSlider'),
  thresholdValueBadge: document.getElementById('thresholdValueBadge'),
  btnRefreshModelInfo: document.getElementById('btnRefreshModelInfo'),
  dashClassChips: document.getElementById('dashClassChips'),
  btnRefreshDashboard: document.getElementById('btnRefreshDashboard'),
  dashKpiTotalIncidents: document.getElementById('dashKpiTotalIncidents'),
  dashKpiTotalViolations: document.getElementById('dashKpiTotalViolations'),
  dashKpiCompliant: document.getElementById('dashKpiCompliant'),
  dashKpiComplianceRate: document.getElementById('dashKpiComplianceRate'),
  dashKpiComplianceBadge: document.getElementById('dashKpiComplianceBadge'),
  dashKpiCritical: document.getElementById('dashKpiCritical'),
  dashKpiModelStatus: document.getElementById('dashKpiModelStatus'),
  dashKpiModelSub: document.getElementById('dashKpiModelSub'),
  dashSpecDevice: document.getElementById('dashSpecDevice'),
  dashRecentIncidentsBody: document.getElementById('dashRecentIncidentsBody'),
  toastContainer: document.getElementById('toastContainer'),

  // Phase 3: Analytics Elements
  btnRefreshAnalytics: document.getElementById('btnRefreshAnalytics'),
  analyticsStartDate: document.getElementById('analyticsStartDate'),
  analyticsEndDate: document.getElementById('analyticsEndDate'),
  analyticsCategory: document.getElementById('analyticsCategory'),
  analyticsSeverity: document.getElementById('analyticsSeverity'),
  analyticsSource: document.getElementById('analyticsSource'),
  btnApplyAnalyticsFilters: document.getElementById('btnApplyAnalyticsFilters'),
  btnResetAnalyticsFilters: document.getElementById('btnResetAnalyticsFilters'),
  kpiTotalIncidents: document.getElementById('kpiTotalIncidents'),
  kpiTotalViolations: document.getElementById('kpiTotalViolations'),
  kpiCompliantDetections: document.getElementById('kpiCompliantDetections'),
  kpiComplianceRate: document.getElementById('kpiComplianceRate'),
  kpiComplianceBadge: document.getElementById('kpiComplianceBadge'),
  kpiComplianceSubtext: document.getElementById('kpiComplianceSubtext'),
  kpiCriticalIncidents: document.getElementById('kpiCriticalIncidents'),
  kpiResolvedIncidents: document.getElementById('kpiResolvedIncidents'),

  // Phase 3: Incident History & Resolution Elements
  incidentSearchInput: document.getElementById('incidentSearchInput'),
  incidentFilterCategory: document.getElementById('incidentFilterCategory'),
  incidentFilterSeverity: document.getElementById('incidentFilterSeverity'),
  incidentFilterSource: document.getElementById('incidentFilterSource'),
  incidentFilterStatus: document.getElementById('incidentFilterStatus'),
  incidentStartDate: document.getElementById('incidentStartDate'),
  incidentEndDate: document.getElementById('incidentEndDate'),
  btnFilterIncidents: document.getElementById('btnFilterIncidents'),
  btnResetIncidentFilters: document.getElementById('btnResetIncidentFilters'),
  btnExportIncidentsCsv: document.getElementById('btnExportIncidentsCsv'),
  incidentsAuditTableBody: document.getElementById('incidentsAuditTableBody'),
  incidentTableCountSummary: document.getElementById('incidentTableCountSummary'),
  incidentPageSize: document.getElementById('incidentPageSize'),
  btnPrevPage: document.getElementById('btnPrevPage'),
  btnNextPage: document.getElementById('btnNextPage'),
  pageIndicator: document.getElementById('pageIndicator'),

  // Phase 3: Incident Detail Modal
  incidentDetailModal: document.getElementById('incidentDetailModal'),
  incidentDetailCloseBtn: document.getElementById('incidentDetailCloseBtn'),
  modalIncidentCancelBtn: document.getElementById('modalIncidentCancelBtn'),
  modalIncidentSaveBtn: document.getElementById('modalIncidentSaveBtn'),
  modalIncidentIdBadge: document.getElementById('modalIncidentIdBadge'),
  modalIncidentEvidenceImg: document.getElementById('modalIncidentEvidenceImg'),
  modalIncidentDownloadBtn: document.getElementById('modalIncidentDownloadBtn'),
  modalIncidentViolation: document.getElementById('modalIncidentViolation'),
  modalIncidentSeverity: document.getElementById('modalIncidentSeverity'),
  modalIncidentConfidence: document.getElementById('modalIncidentConfidence'),
  modalIncidentSource: document.getElementById('modalIncidentSource'),
  modalIncidentTimestamp: document.getElementById('modalIncidentTimestamp'),
  modalResolutionStatus: document.getElementById('modalResolutionStatus'),
  modalResolutionNotes: document.getElementById('modalResolutionNotes'),
  modalResolvedMeta: document.getElementById('modalResolvedMeta'),
  modalResolvedTime: document.getElementById('modalResolvedTime'),

  // Phase 3: Reports Elements
  reportGenerationForm: document.getElementById('reportGenerationForm'),
  reportTypeSelect: document.getElementById('reportTypeSelect'),
  reportCustomDateRow: document.getElementById('reportCustomDateRow'),
  reportStartDate: document.getElementById('reportStartDate'),
  reportEndDate: document.getElementById('reportEndDate'),
  reportSeveritySelect: document.getElementById('reportSeveritySelect'),
  reportCategorySelect: document.getElementById('reportCategorySelect'),
  formatCardPdf: document.getElementById('formatCardPdf'),
  formatCardCsv: document.getElementById('formatCardCsv'),
  btnGenerateReport: document.getElementById('btnGenerateReport'),
  btnRefreshReportsHistory: document.getElementById('btnRefreshReportsHistory'),
  reportsHistoryTableBody: document.getElementById('reportsHistoryTableBody'),

  // Phase 3: Settings Elements
  settingsConfThreshold: document.getElementById('settingsConfThreshold'),
  settingsConfBadge: document.getElementById('settingsConfBadge'),
  settingsFrameStride: document.getElementById('settingsFrameStride'),
  settingsCooldown: document.getElementById('settingsCooldown'),
  settingsMinSeverity: document.getElementById('settingsMinSeverity'),
  settingsFacilityName: document.getElementById('settingsFacilityName'),
  btnSaveSystemSettings: document.getElementById('btnSaveSystemSettings'),
  btnRefreshDiagnostics: document.getElementById('btnRefreshDiagnostics'),
  diagDbSize: document.getElementById('diagDbSize'),
  diagStorageSize: document.getElementById('diagStorageSize'),
  diagTotalIncidents: document.getElementById('diagTotalIncidents'),
  diagTotalVideos: document.getElementById('diagTotalVideos'),
  diagTotalReports: document.getElementById('diagTotalReports'),
  diagBackendStatus: document.getElementById('diagBackendStatus'),
  diagDbStatus: document.getElementById('diagDbStatus')
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupTopbarAndModals();
  setupDashboardModule();
  setupImageDetectionModule();
  setupVideoDetectionModule();
  setupLiveMonitoringModule();
  setupAlertsModule();
  setupAnalyticsModule();
  setupIncidentHistoryModule();
  setupReportsModule();
  setupSettingsModule();
  loadDashboard();
  fetchModelInfo();
  fetchSurveillanceStats();
  loadIncidents();
});

// ============================================================================
// NAVIGATION CONTROLLER
// ============================================================================
function setupNavigation() {
  document.querySelectorAll('[data-view]').forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      navigateTo(targetView);
    });
  });

  // Mobile sidebar toggle
  elements.sidebarToggle.addEventListener('click', () => {
    elements.sidebar.classList.toggle('mobile-open');
  });
}

window.navigateTo = function(viewName) {
  state.currentView = viewName;

  // Active view switching
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  const target = document.getElementById(`view-${viewName}`);
  if (target) {
    target.classList.add('active');
  }

  // Update sidebar active highlights
  document.querySelectorAll('.nav-item, .nav-sub-item').forEach(item => {
    item.classList.remove('active');
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    }
  });

  elements.sidebar.classList.remove('mobile-open');
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger view-specific loads
  if (viewName === 'analytics') {
    loadAnalytics();
  } else if (viewName === 'incident-history') {
    loadIncidentAuditTable();
  } else if (viewName === 'reports') {
    loadReportsHistory();
  } else if (viewName === 'settings') {
    loadSystemSettings();
    loadStorageDiagnostics();
  } else if (viewName === 'alerts') {
    loadIncidents();
  } else if (viewName === 'dashboard') {
    loadDashboard();
    fetchModelInfo();
  } else if (viewName === 'model-info') {
    fetchModelInfo();
  }
};

// ============================================================================
// TOPBAR & MODALS
// ============================================================================
function setupTopbarAndModals() {
  elements.profileDropdown.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.profileMenu.classList.toggle('show');
  });
  document.addEventListener('click', () => {
    elements.profileMenu.classList.remove('show');
  });

  elements.infoBtn.addEventListener('click', () => {
    elements.infoModal.style.display = 'flex';
  });
  elements.modalCloseBtn.addEventListener('click', () => {
    elements.infoModal.style.display = 'none';
  });
  elements.modalOkBtn.addEventListener('click', () => {
    elements.infoModal.style.display = 'none';
  });

  elements.evidenceModalCloseBtn.addEventListener('click', () => {
    elements.evidenceModal.style.display = 'none';
  });
}

window.openEvidenceModal = function(imgUrl, incidentId, violation, time) {
  elements.evidenceModalImg.src = imgUrl;
  elements.evidenceDownloadBtn.href = imgUrl;
  elements.evidenceModalMeta.innerHTML = `
    <strong>Incident ID:</strong> ${incidentId}<br>
    <strong>Violation:</strong> <span class="tag-violation-red">${violation}</span><br>
    <strong>Timestamp:</strong> ${time}
  `;
  elements.evidenceModal.style.display = 'flex';
};

// ============================================================================
// EXECUTIVE DASHBOARD MODULE
// ============================================================================
function setupDashboardModule() {
  if (elements.btnRefreshDashboard) {
    elements.btnRefreshDashboard.addEventListener('click', () => {
      loadDashboard();
      showToast('Dashboard refreshed with latest surveillance data.', 'info');
    });
  }
}

async function loadDashboard() {
  try {
    const [overviewRes, trendsRes, violationsRes, recentRes, modelRes] = await Promise.all([
      fetch('/api/analytics/overview?time_range=30d'),
      fetch('/api/analytics/trends?days=7'),
      fetch('/api/analytics/violations?time_range=30d'),
      fetch('/api/incidents?limit=6'),
      fetch('/api/model-info')
    ]);

    if (overviewRes.ok) {
      const data = await overviewRes.json();
      const stats = data.analytics || data;
      if (elements.dashKpiTotalIncidents) elements.dashKpiTotalIncidents.textContent = stats.total_incidents || 0;
      if (elements.dashKpiTotalViolations) elements.dashKpiTotalViolations.textContent = stats.total_violations || stats.violation_detections || 0;
      if (elements.dashKpiCompliant) elements.dashKpiCompliant.textContent = stats.compliant_detections || 0;
      if (elements.dashKpiCritical) elements.dashKpiCritical.textContent = stats.critical_incidents || 0;

      if (elements.dashKpiComplianceRate && elements.dashKpiComplianceBadge) {
        const pct = (stats.compliance_percentage !== undefined && stats.compliance_percentage !== null)
          ? stats.compliance_percentage
          : (typeof stats.compliance_rate === 'number' ? stats.compliance_rate : null);
        if (pct !== null) {
          elements.dashKpiComplianceRate.textContent = `${pct.toFixed(1)}%`;
          if (pct >= 85) {
            elements.dashKpiComplianceBadge.className = 'compliance-badge badge-safe';
            elements.dashKpiComplianceBadge.textContent = 'Compliant';
          } else if (pct >= 70) {
            elements.dashKpiComplianceBadge.className = 'compliance-badge badge-warning';
            elements.dashKpiComplianceBadge.textContent = 'Attention';
          } else {
            elements.dashKpiComplianceBadge.className = 'compliance-badge badge-danger';
            elements.dashKpiComplianceBadge.textContent = 'Violations High';
          }
        } else {
          elements.dashKpiComplianceRate.textContent = stats.compliance_rate || '--%';
        }
      }
    }

    if (modelRes.ok) {
      const minfo = await modelRes.json();
      if (elements.dashKpiModelStatus) elements.dashKpiModelStatus.textContent = minfo.status || 'Ready';
      if (elements.dashKpiModelSub) elements.dashKpiModelSub.textContent = `${minfo.model_name || 'best.pt'} • ${minfo.device || 'CPU'}`;
      if (elements.dashSpecDevice) elements.dashSpecDevice.textContent = minfo.device || 'CPU (Optimized)';

      // Populate class inventory chips
      if (elements.dashClassChips && minfo.classes) {
        elements.dashClassChips.innerHTML = '';
        const classNames = Object.values(minfo.classes);
        classNames.forEach(c => {
          const chip = document.createElement('span');
          const isViol = c.startsWith('no-');
          chip.className = `class-chip ${isViol ? 'violation' : 'compliant'}`;
          chip.innerHTML = `<i class="fa-solid ${isViol ? 'fa-triangle-exclamation' : 'fa-check'}"></i> ${c}`;
          elements.dashClassChips.appendChild(chip);
        });
      }
    }

    if (trendsRes.ok) {
      const tdata = await trendsRes.json();
      renderDashTrendsChart(tdata.trends || []);
    }

    if (violationsRes.ok) {
      const vdata = await violationsRes.json();
      renderDashViolationsChart(vdata.violations || []);
    }

    if (recentRes.ok && elements.dashRecentIncidentsBody) {
      const rdata = await recentRes.json();
      const incidents = rdata.incidents || [];
      elements.dashRecentIncidentsBody.innerHTML = '';
      if (incidents.length === 0) {
        elements.dashRecentIncidentsBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted" style="padding: 24px;">No safety incidents recorded yet.</td></tr>';
      } else {
        incidents.forEach(inc => {
          const tr = document.createElement('tr');
          const isCrit = inc.severity === 'CRITICAL';
          const isHigh = inc.severity === 'HIGH';
          const sevClass = isCrit ? 'severity-pill-critical' : (isHigh ? 'severity-pill-high' : 'severity-pill-medium');
          let statusBadgeClass = 'status-badge-new';
          if (inc.status === 'ACKNOWLEDGED') statusBadgeClass = 'status-badge-ack';
          if (inc.status === 'RESOLVED') statusBadgeClass = 'status-badge-resolved';

          tr.innerHTML = `
            <td><strong class="font-mono text-purple">${inc.incident_id}</strong></td>
            <td><span class="tag-violation-red">${inc.violation_category}</span></td>
            <td class="font-mono">${(inc.confidence * 100).toFixed(0)}%</td>
            <td><span class="${sevClass}">${inc.severity}</span></td>
            <td>${formatSourceLabel(inc.source)}</td>
            <td class="font-mono text-muted" style="font-size: 0.75rem;">${inc.timestamp}</td>
            <td class="text-center">
              <img src="${inc.evidence_path}" class="evidence-tiny-thumb" alt="Evidence" onclick="openIncidentDetailModal('${inc.incident_id}')">
            </td>
            <td><span class="${statusBadgeClass}">${inc.status}</span></td>
            <td style="text-align: right;">
              <button class="btn btn-outline btn-sm" onclick="openIncidentDetailModal('${inc.incident_id}')">
                <i class="fa-solid fa-file-pen"></i> Resolve
              </button>
            </td>
          `;
          elements.dashRecentIncidentsBody.appendChild(tr);
        });
      }
    }
  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

function renderDashTrendsChart(timeline) {
  const canvas = document.getElementById('dashChartTrends');
  if (!canvas || typeof Chart === 'undefined') return;
  if (state.charts.dashTrends) state.charts.dashTrends.destroy();

  const labels = timeline.map(t => t.date);
  const counts = timeline.map(t => t.count);

  state.charts.dashTrends = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['No Data'],
      datasets: [{
        label: 'Incident Velocity',
        data: counts.length ? counts : [0],
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.08)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#4f46e5',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#f1f5f9' } },
        x: { ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } }, grid: { display: false } }
      }
    }
  });
}

function renderDashViolationsChart(categories) {
  const canvas = document.getElementById('dashChartViolations');
  if (!canvas || typeof Chart === 'undefined') return;
  if (state.charts.dashViolations) state.charts.dashViolations.destroy();

  const labels = categories.map(c => c.category);
  const counts = categories.map(c => c.count);
  const colors = labels.map(label => {
    const l = label.toLowerCase();
    if (l.includes('helmet')) return '#ef4444';
    if (l.includes('vest')) return '#f97316';
    if (l.includes('gloves')) return '#3b82f6';
    if (l.includes('goggles')) return '#8b5cf6';
    if (l.includes('boots')) return '#10b981';
    return '#6366f1';
  });

  state.charts.dashViolations = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Helmet', 'Vest', 'Gloves', 'Goggles', 'Boots'],
      datasets: [{
        label: 'Violations',
        data: counts.length ? counts : [0, 0, 0, 0, 0],
        backgroundColor: colors.length ? colors : ['#ef4444', '#f97316', '#3b82f6', '#8b5cf6', '#10b981'],
        borderRadius: 6,
        barThickness: 24
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#f1f5f9' } },
        x: { ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } }, grid: { display: false } }
      }
    }
  });
}

// ============================================================================
// BACKEND MODEL API CONNECTION
// ============================================================================
async function fetchModelInfo() {
  try {
    const res = await fetch('/api/model-info');
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    state.modelInfo = data;
    state.isModelReady = data.status === 'Ready';

    if (state.isModelReady) {
      elements.topModelStatus.className = 'model-status-indicator status-ready';
      elements.topModelLabel.textContent = 'Model Ready';
      elements.topModelIcon.className = 'fa-solid fa-circle-check status-icon';
      populateModelSpecs(data);
    }
  } catch (err) {
    console.error('Failed to connect to backend model API:', err);
    elements.topModelStatus.className = 'model-status-indicator status-error';
    elements.topModelLabel.textContent = 'Connection Error';
    elements.topModelIcon.className = 'fa-solid fa-triangle-exclamation status-icon';
  }
}

async function fetchSurveillanceStats() {
  try {
    const res = await fetch('/api/surveillance/stats');
    if (!res.ok) return;
    const json = await res.json();
    const stats = json.stats;
    if (elements.metricVideosAnalyzed) {
      elements.metricVideosAnalyzed.textContent = stats.videos_analyzed || 0;
    }
    if (!state.isVideoProcessing && !state.activeVideoJobId) {
      if (elements.metricVideoTotalDetections) {
        elements.metricVideoTotalDetections.textContent = (stats.total_detections || 0).toLocaleString();
      }
      if (elements.metricVideoViolations) {
        elements.metricVideoViolations.textContent = (stats.total_violations ?? stats.safety_violations ?? 0).toLocaleString();
      }
      if (elements.metricComplianceRate) {
        elements.metricComplianceRate.textContent = stats.compliance_rate || 'Not enough data';
      }
    }
  } catch (err) {
    console.error('Failed to load surveillance stats:', err);
  }
}

function populateModelSpecs(data) {
  if (elements.specModelName) elements.specModelName.textContent = data.model_name || 'best.pt';
  if (elements.specModelPath) elements.specModelPath.textContent = data.model_path || 'se_project/models/best.pt';
  if (elements.specArchitecture) elements.specArchitecture.textContent = data.architecture || 'YOLO (DetectionModel)';
  if (elements.specDevice) elements.specDevice.textContent = data.device || 'CPU (Optimized)';
  if (elements.specStatus) elements.specStatus.textContent = data.status === 'Ready' ? 'Ready & Loaded' : 'Error';

  if (data.classes && elements.specsClassesTableBody) {
    elements.specsClassesTableBody.innerHTML = '';
    Object.entries(data.classes).forEach(([id, name]) => {
      const isViolation = name.startsWith('no-');
      const category = isViolation ? 'Safety Violation' : 'Compliant PPE';
      const colorHex = isViolation ? '#ef4444' : '#10b981';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong class="font-mono">${id}</strong></td>
        <td><span class="${isViolation ? 'tag-violation-red' : 'tag-helmet'}">${name}</span></td>
        <td><strong>${category}</strong></td>
        <td><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:${colorHex};vertical-align:middle;margin-right:6px;"></span> ${colorHex}</td>
        <td class="text-muted">${getIndustrialPurpose(name)}</td>
      `;
      elements.specsClassesTableBody.appendChild(tr);
    });
  }

  if (data.classes && elements.dashClassChips) {
    elements.dashClassChips.innerHTML = '';
    Object.entries(data.classes).forEach(([id, name]) => {
      const isViolation = name.startsWith('no-');
      const chip = document.createElement('div');
      chip.className = `class-chip ${isViolation ? 'tag-violation' : 'tag-helmet'}`;
      chip.innerHTML = `<i class="fa-solid ${isViolation ? 'fa-triangle-exclamation' : 'fa-check'}"></i> <span>${name}</span>`;
      elements.dashClassChips.appendChild(chip);
    });
  }
}

function getIndustrialPurpose(className) {
  const map = {
    'boots': 'Foot crush protection in heavy construction areas',
    'gloves': 'Hand protection against abrasions and chemicals',
    'goggles': 'Eye protection from flying debris and sparks',
    'helmet': 'Head impact protection against falling objects',
    'vest': 'High-visibility safety apparel for transit zones',
    'no-boots': 'Violation: Missing mandatory protective safety boots',
    'no-gloves': 'Violation: Missing mandatory hand safety equipment',
    'no-goggles': 'Violation: Missing required eye & face protective gear',
    'no-helmet': 'Violation: Critical missing hard hat in PPE zone',
    'no-vest': 'Violation: Worker lacks high-visibility reflection vest'
  };
  return map[className] || 'Industrial safety monitoring component';
}

// ============================================================================
// VIDEO DETECTION MODULE (PHASE 2 - MATCHING EXACT REFERENCE DESIGN)
// ============================================================================
function setupVideoDetectionModule() {
  // Choose Video Button
  elements.chooseVideoBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.videoFileInput.click();
  });

  elements.videoDropZone.addEventListener('click', () => {
    if (!state.selectedVideoFile) elements.videoFileInput.click();
  });

  elements.videoFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleVideoSelected(e.target.files[0]);
    }
  });

  // Drag and drop for video
  ['dragenter', 'dragover'].forEach(name => {
    elements.videoDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.videoDropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    elements.videoDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.videoDropZone.classList.remove('dragover');
    });
  });

  elements.videoDropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleVideoSelected(e.dataTransfer.files[0]);
    }
  });

  // Remove Staged Video
  elements.btnRemoveStagedVideo.addEventListener('click', (e) => {
    e.stopPropagation();
    clearVideoStaging();
  });

  // Quick Demo: Load factory_shift.mp4
  elements.loadSampleVideoBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    try {
      const res = await fetch('/assets/videos/factory_shift.mp4');
      if (!res.ok) throw new Error('factory_shift.mp4 not found.');
      const blob = await res.blob();
      const file = new File([blob], 'factory_shift.mp4', { type: 'video/mp4' });
      handleVideoSelected(file);
      showToast('Loaded demo video "factory_shift.mp4".', 'info');
    } catch (err) {
      showToast('Could not load demo video: ' + err.message, 'error');
    }
  });

  // Video Controls: Play / Pause
  elements.ctrlPlayPause.addEventListener('click', () => {
    const v = elements.mainSurveillanceVideo;
    if (v.paused) {
      v.play();
      elements.ctrlPlayPause.innerHTML = '<i class="fa-solid fa-pause"></i>';
    } else {
      v.pause();
      elements.ctrlPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
    }
  });

  elements.ctrlStop.addEventListener('click', () => {
    const v = elements.mainSurveillanceVideo;
    v.pause();
    v.currentTime = 0;
    elements.ctrlPlayPause.innerHTML = '<i class="fa-solid fa-play"></i>';
  });

  // Video Time Update & Scrubber
  elements.mainSurveillanceVideo.addEventListener('timeupdate', () => {
    const v = elements.mainSurveillanceVideo;
    if (v.duration) {
      const pct = (v.currentTime / v.duration) * 100;
      elements.scrubberFill.style.width = `${pct}%`;
      elements.videoTimer.textContent = `${formatTime(v.currentTime)} / ${formatTime(v.duration)}`;
    }
  });

  elements.videoScrubber.addEventListener('click', (e) => {
    const rect = elements.videoScrubber.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    const v = elements.mainSurveillanceVideo;
    if (v.duration) {
      v.currentTime = pos * v.duration;
    }
  });

  // Volume
  elements.ctrlVolume.addEventListener('click', () => {
    const v = elements.mainSurveillanceVideo;
    v.muted = !v.muted;
    elements.ctrlVolume.innerHTML = v.muted ? '<i class="fa-solid fa-volume-xmark"></i>' : '<i class="fa-solid fa-volume-high"></i>';
  });

  // Fullscreen
  elements.ctrlFullscreen.addEventListener('click', () => {
    const container = document.getElementById('videoPlayerContainer');
    if (!document.fullscreenElement) {
      container.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  });

  // Action Buttons
  elements.btnAnalyzeVideo.addEventListener('click', () => {
    startVideoAnalysis();
  });

  elements.btnClearVideo.addEventListener('click', () => {
    clearVideoStaging();
    showToast('Video detection workspace reset.', 'info');
  });

  elements.btnDownloadVideoResult.addEventListener('click', () => {
    if (state.annotatedVideoUrl) {
      const a = document.createElement('a');
      a.href = state.annotatedVideoUrl;
      a.download = `annotated_${Date.now()}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      showToast('Annotated video ready. Downloading result.', 'success');
      const a = document.createElement('a');
      a.href = '/assets/videos/factory_shift.mp4';
      a.download = 'annotated_factory_shift.mp4';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  });
}

function handleVideoSelected(file) {
  state.selectedVideoFile = file;

  // Update Staged card details
  elements.stagedVideoName.textContent = file.name;
  elements.stagedVideoMeta.textContent = `Size: ${(file.size / (1024 * 1024)).toFixed(1)} MB`;

  const videoUrl = URL.createObjectURL(file);
  elements.mainSurveillanceVideo.src = videoUrl;
  elements.mainSurveillanceVideo.load();

  elements.mainSurveillanceVideo.onloadedmetadata = () => {
    const dur = formatTime(elements.mainSurveillanceVideo.duration);
    const res = `${elements.mainSurveillanceVideo.videoWidth || 1280} × ${elements.mainSurveillanceVideo.videoHeight || 720}`;
    elements.stagedVideoMeta.innerHTML = `Duration: ${dur}<br>Resolution: ${res}`;
    elements.videoTimer.textContent = `00:00:00 / ${dur}`;
  };

  elements.stagedVideoPillCard.style.display = 'flex';
  elements.btnAnalyzeVideo.disabled = false;
}

function clearVideoStaging() {
  state.selectedVideoFile = null;
  state.activeVideoJobId = null;
  clearInterval(state.videoPollingInterval);

  elements.videoFileInput.value = '';
  elements.mainSurveillanceVideo.pause();
  elements.mainSurveillanceVideo.src = '';
  elements.stagedVideoPillCard.style.display = 'none';
  elements.videoProcessingOverlay.style.display = 'none';
  elements.btnAnalyzeVideo.disabled = true;

  // Reset table & details
  if (elements.countHelmet) elements.countHelmet.textContent = '0';
  if (elements.countVest) elements.countVest.textContent = '0';
  if (elements.countGloves) elements.countGloves.textContent = '0';
  if (elements.countGoggles) elements.countGoggles.textContent = '0';
  if (elements.countBoots) elements.countBoots.textContent = '0';
  if (elements.countViolations) elements.countViolations.textContent = '0';
  if (elements.countHelmetFrames) elements.countHelmetFrames.textContent = '0';
  if (elements.countVestFrames) elements.countVestFrames.textContent = '0';
  if (elements.countGlovesFrames) elements.countGlovesFrames.textContent = '0';
  if (elements.countGogglesFrames) elements.countGogglesFrames.textContent = '0';
  if (elements.countBootsFrames) elements.countBootsFrames.textContent = '0';
  if (elements.countViolationsFrames) elements.countViolationsFrames.textContent = '0';
  if (elements.detailTotalFrames) elements.detailTotalFrames.textContent = '—';
  if (elements.detailFramesProcessed) elements.detailFramesProcessed.textContent = '—';
  if (elements.detailProcessingFps) elements.detailProcessingFps.textContent = '—';
  if (elements.detailTotalDetections) elements.detailTotalDetections.textContent = '—';
  if (elements.detailUniqueObjects) elements.detailUniqueObjects.textContent = '—';
  if (elements.detailTotalViolations) elements.detailTotalViolations.textContent = '—';
  if (elements.detailProcessingTime) elements.detailProcessingTime.textContent = '—';
  if (elements.timelineTableBody) {
    elements.timelineTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding: 24px;">No safety violations detected in this video. All safety protocols compliant!</td></tr>';
  }
}

async function startVideoAnalysis() {
  if (!state.selectedVideoFile) {
    // If user clicked without staging file, auto-load factory_shift.mp4
    try {
      const res = await fetch('/assets/videos/factory_shift.mp4');
      const blob = await res.blob();
      state.selectedVideoFile = new File([blob], 'factory_shift.mp4', { type: 'video/mp4' });
    } catch (e) {}
  }

  state.isVideoProcessing = true;
  elements.videoProcessingOverlay.style.display = 'flex';
  elements.btnAnalyzeVideo.disabled = true;
  elements.videoAnalysisStatusPill.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Analyzing Video...</span>';

  const formData = new FormData();
  formData.append('file', state.selectedVideoFile);

  try {
    const res = await fetch('/api/detect/video?confidence=0.15&frame_stride=4', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error('Failed to initiate video processing.');
    const data = await res.json();
    state.activeVideoJobId = data.job_id;

    // Start polling status
    pollVideoJobProgress(data.job_id);
    showToast('Video analysis initiated with YOLO frame sampling.', 'info');
  } catch (err) {
    console.error('Video analysis error:', err);
    state.isVideoProcessing = false;
    elements.videoProcessingOverlay.style.display = 'none';
    elements.btnAnalyzeVideo.disabled = false;
    showToast('Video processing failed: ' + err.message, 'error');
  }
}

function pollVideoJobProgress(jobId) {
  state.videoPollingInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/video/status/${jobId}`);
      if (!res.ok) return;
      const json = await res.json();
      const job = json.job;

      // Update overlay progress
      elements.overlayProgressFill.style.width = `${job.progress}%`;
      elements.videoProcessingText.textContent = `Analyzing Frames: ${job.current_frame} / ${job.total_frames} (${Math.round(job.progress)}%)`;

      // Update processing details
      elements.detailTotalFrames.textContent = (job.total_frames || 0).toLocaleString();
      elements.detailFramesProcessed.textContent = (job.current_frame || 0).toLocaleString();
      elements.detailProcessingFps.textContent = (job.processing_fps || 0).toFixed(1);
      if (elements.detailTotalDetections) {
        elements.detailTotalDetections.textContent = (job.total_frame_detections || job.total_detections || 0).toLocaleString();
      }
      if (elements.detailUniqueObjects) {
        elements.detailUniqueObjects.textContent = (job.total_unique_objects != null ? job.total_unique_objects : (job.unique_tracked_objects || 0)).toLocaleString();
      }
      elements.detailTotalViolations.textContent = (job.total_unique_violations != null ? job.total_unique_violations : (job.unique_violations != null ? job.unique_violations : (job.total_violations || 0))).toLocaleString();
      elements.detailProcessingTime.textContent = `${Math.floor(job.elapsed_time / 60)}:${Math.floor(job.elapsed_time % 60).toString().padStart(2, '0')} min`;

      // Top metric cards (Updated live with tracking results)
      if (elements.metricVideoTotalDetections) {
        elements.metricVideoTotalDetections.textContent = (job.total_frame_detections || job.total_detections || 0).toLocaleString();
      }
      if (elements.metricVideoUniqueObjects) {
        elements.metricVideoUniqueObjects.textContent = (job.total_unique_objects != null ? job.total_unique_objects : (job.unique_tracked_objects || 0)).toLocaleString();
      }
      if (elements.metricVideoViolations) {
        elements.metricVideoViolations.textContent = (job.total_unique_violations != null ? job.total_unique_violations : (job.unique_violations != null ? job.unique_violations : (job.total_violations || 0))).toLocaleString();
      }
      if (job.compliance_rate != null && elements.metricComplianceRate) {
        elements.metricComplianceRate.textContent = `${job.compliance_rate}%`;
      }

      // Detection Summary table: Frame Detections vs Unique Tracked Objects
      const fc = job.frame_class_counts || job.class_counts || {};
      const uc = job.unique_class_counts || {};

      // A. Frame counts
      if (elements.countHelmetFrames) elements.countHelmetFrames.textContent = (fc['helmet'] || 0).toLocaleString();
      if (elements.countVestFrames) elements.countVestFrames.textContent = (fc['vest'] || 0).toLocaleString();
      if (elements.countGlovesFrames) elements.countGlovesFrames.textContent = (fc['gloves'] || 0).toLocaleString();
      if (elements.countGogglesFrames) elements.countGogglesFrames.textContent = (fc['goggles'] || 0).toLocaleString();
      if (elements.countBootsFrames) elements.countBootsFrames.textContent = (fc['boots'] || 0).toLocaleString();
      const frameViolations = (fc['no-helmet'] || 0) + (fc['no-vest'] || 0) + (fc['no-gloves'] || 0) + (fc['no-goggles'] || 0) + (fc['no-boots'] || 0);
      if (elements.countViolationsFrames) elements.countViolationsFrames.textContent = frameViolations.toLocaleString();

      // B. Unique tracked objects
      if (elements.countHelmet) elements.countHelmet.textContent = (uc['helmet'] != null ? uc['helmet'] : (job.unique_helmets || 0)).toLocaleString();
      if (elements.countVest) elements.countVest.textContent = (uc['vest'] != null ? uc['vest'] : (job.unique_vests || 0)).toLocaleString();
      if (elements.countGloves) elements.countGloves.textContent = (uc['gloves'] != null ? uc['gloves'] : (job.unique_gloves || 0)).toLocaleString();
      if (elements.countGoggles) elements.countGoggles.textContent = (uc['goggles'] != null ? uc['goggles'] : (job.unique_goggles || 0)).toLocaleString();
      if (elements.countBoots) elements.countBoots.textContent = (uc['boots'] != null ? uc['boots'] : (job.unique_boots || 0)).toLocaleString();
      const uniqueViolations = (uc['no-helmet'] || 0) + (uc['no-vest'] || 0) + (uc['no-gloves'] || 0) + (uc['no-goggles'] || 0) + (uc['no-boots'] || 0);
      if (elements.countViolations) elements.countViolations.textContent = (job.total_unique_violations != null ? job.total_unique_violations : uniqueViolations).toLocaleString();

      if (job.status === 'completed' || job.status === 'stopped' || job.status === 'failed') {
        clearInterval(state.videoPollingInterval);
        state.isVideoProcessing = false;
        elements.videoProcessingOverlay.style.display = 'none';
        elements.btnAnalyzeVideo.disabled = false;

        if (job.status === 'completed') {
          elements.videoAnalysisStatusPill.style.display = 'flex';
          elements.videoAnalysisStatusPill.innerHTML = '<i class="fa-solid fa-check"></i> <span>Processing Completed</span>';
          elements.analysisCompletedBadge.style.display = 'flex';
          state.annotatedVideoUrl = job.annotated_video_url;

          // Play annotated video if available
          if (job.annotated_video_url) {
            elements.mainSurveillanceVideo.src = `${job.annotated_video_url}?t=${Date.now()}`;
            elements.mainSurveillanceVideo.play().catch(() => {});
          }

          renderTimelineViolations(job.violations_summary);
          loadIncidents(); // Refresh alerts table
          fetchSurveillanceStats(); // Refresh video records count
          showToast(`Video surveillance complete! Found ${job.total_unique_violations != null ? job.total_unique_violations : job.total_violations} unique safety violations (${job.total_frame_detections || job.total_detections} total frame detections).`, 'success');
        }
      }
    } catch (e) {
      console.error('Polling error:', e);
    }
  }, 600);
}

function renderTimelineViolations(violations) {
  if (!elements.timelineTableBody) return;
  elements.timelineTableBody.innerHTML = '';

  if (!violations || violations.length === 0) {
    elements.timelineTableBody.innerHTML = `
      <tr><td colspan="6" class="text-center text-muted" style="padding: 24px;">No safety violations detected in this video. All safety protocols compliant!</td></tr>
    `;
    return;
  }

  violations.forEach((v, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td class="font-mono">${v.timestamp || '00:00:00'}</td>
      <td><span class="tag-violation-red">${v.violation}</span></td>
      <td class="font-mono">${typeof v.confidence === 'number' ? v.confidence.toFixed(2) : v.confidence}</td>
      <td><span class="${v.severity === 'CRITICAL' ? 'severity-pill-critical' : (v.severity === 'HIGH' ? 'severity-pill-high' : 'severity-pill-medium')}">${v.severity}</span></td>
      <td class="text-center">
        <img src="${v.evidence_url}" class="evidence-tiny-thumb" alt="Evidence" onclick="openEvidenceModal('${v.evidence_url}', '${v.incident_id}', '${v.violation}', '${v.timestamp}')">
      </td>
    `;
    elements.timelineTableBody.appendChild(tr);
  });
}

function formatTime(sec) {
  const s = Math.floor(sec || 0);
  const m = Math.floor(s / 60);
  const remS = s % 60;
  return `00:${m.toString().padStart(2, '0')}:${remS.toString().padStart(2, '0')}`;
}

// ============================================================================
// LIVE MONITORING MODULE (WEBCAM & CCTV)
// ============================================================================
function setupLiveMonitoringModule() {
  elements.btnStartCamera.addEventListener('click', () => {
    startLiveWebcam();
  });

  elements.btnStopCamera.addEventListener('click', () => {
    stopLiveWebcam();
  });

  elements.btnPauseCameraStream.addEventListener('click', () => {
    state.isLiveInferencePaused = !state.isLiveInferencePaused;
    elements.btnPauseCameraStream.innerHTML = state.isLiveInferencePaused
      ? '<i class="fa-solid fa-play"></i> Resume Inference'
      : '<i class="fa-solid fa-pause"></i> Pause Inference';
    showToast(state.isLiveInferencePaused ? 'Live inference paused.' : 'Live inference resumed.', 'info');
  });

  elements.btnClearLiveAlerts.addEventListener('click', () => {
    elements.liveAlertsScroll.innerHTML = '';
  });
}

async function startLiveWebcam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });

    state.webcamStream = stream;
    state.isLiveMonitoring = true;
    state.isLiveInferencePaused = false;

    elements.webcamVideo.srcObject = stream;
    elements.liveOfflineOverlay.style.display = 'none';
    elements.liveIndicatorPill.style.display = 'flex';
    elements.liveCameraStatus.textContent = 'Active (Live)';
    elements.liveCameraStatus.style.color = '#10b981';

    elements.btnStartCamera.disabled = true;
    elements.btnStopCamera.disabled = false;
    elements.btnPauseCameraStream.disabled = false;

    // Register live session on backend
    fetch('/api/live/start', { method: 'POST' }).catch(() => {});

    // Begin periodic frame inference (every 600ms)
    startLiveInferenceLoop();
    showToast('Webcam surveillance feed active.', 'success');
  } catch (err) {
    console.error('Webcam access failed:', err);
    showToast('Webcam access error: ' + err.message, 'error');
  }
}

let isLiveInferencing = false;
let liveFrameTimeoutId = null;

function stopLiveWebcam() {
  if (state.webcamStream) {
    state.webcamStream.getTracks().forEach(track => track.stop());
    state.webcamStream = null;
  }

  state.isLiveMonitoring = false;
  isLiveInferencing = false;
  if (liveFrameTimeoutId) {
    clearTimeout(liveFrameTimeoutId);
    liveFrameTimeoutId = null;
  }

  elements.webcamVideo.srcObject = null;
  elements.liveOfflineOverlay.style.display = 'flex';
  elements.liveIndicatorPill.style.display = 'none';
  elements.liveCameraStatus.textContent = 'Offline';
  elements.liveCameraStatus.style.color = '#ef4444';
  elements.liveFeedFps.textContent = '0 FPS';
  elements.liveCurrentDetections.textContent = '0';

  elements.btnStartCamera.disabled = false;
  elements.btnStopCamera.disabled = true;
  elements.btnPauseCameraStream.disabled = true;

  // Clear overlay canvas
  const ctx = elements.webcamCanvasOverlay.getContext('2d');
  ctx.clearRect(0, 0, elements.webcamCanvasOverlay.width, elements.webcamCanvasOverlay.height);

  fetch('/api/live/stop', { method: 'POST' }).catch(() => {});
  showToast('Webcam stream stopped.', 'info');
}

function startLiveInferenceLoop() {
  if (liveFrameTimeoutId) {
    clearTimeout(liveFrameTimeoutId);
    liveFrameTimeoutId = null;
  }
  isLiveInferencing = false;

  async function processNextLiveFrame() {
    if (!state.isLiveMonitoring) return;
    if (state.isLiveInferencePaused) {
      liveFrameTimeoutId = setTimeout(processNextLiveFrame, 300);
      return;
    }

    const video = elements.webcamVideo;
    if (!video || video.readyState < 2 || isLiveInferencing) {
      liveFrameTimeoutId = setTimeout(processNextLiveFrame, 100);
      return;
    }

    isLiveInferencing = true;
    try {
      const overlayCanvas = elements.webcamCanvasOverlay;
      const offscreen = elements.offscreenCanvas;
      const offCtx = offscreen.getContext('2d');

      // Efficient resolution downscale for low-latency network transfer and fast CPU YOLO inference
      const targetW = 480;
      const targetH = 360;
      offscreen.width = targetW;
      offscreen.height = targetH;
      offCtx.drawImage(video, 0, 0, targetW, targetH);

      // Match overlay canvas to true video display dimensions
      const dispW = video.videoWidth || 640;
      const dispH = video.videoHeight || 480;
      overlayCanvas.width = dispW;
      overlayCanvas.height = dispH;

      const scaleX = dispW / targetW;
      const scaleY = dispH / targetH;

      const blob = await new Promise(resolve => offscreen.toBlob(resolve, 'image/jpeg', 0.8));
      if (blob && state.isLiveMonitoring) {
        const formData = new FormData();
        formData.append('file', blob, 'live_frame.jpg');

        const start = performance.now();
        const res = await fetch(`/api/live/detect-frame?confidence=${state.confThreshold}`, {
          method: 'POST',
          body: formData
        });

        if (res.ok && state.isLiveMonitoring) {
          const data = await res.json();
          const elapsed = (performance.now() - start) / 1000;
          const fps = Math.min(30, Math.round(1 / Math.max(0.04, elapsed)));
          elements.liveFeedFps.textContent = `${fps} FPS`;
          elements.liveCurrentDetections.textContent = data.total_detections;

          // Scale coordinates back to overlay display dimensions accurately
          const scaledDetections = (data.detections || []).map(d => ({
            ...d,
            bbox: [
              Math.round(d.bbox[0] * scaleX),
              Math.round(d.bbox[1] * scaleY),
              Math.round(d.bbox[2] * scaleX),
              Math.round(d.bbox[3] * scaleY)
            ]
          }));

          drawBoundingBoxesOnCanvas(overlayCanvas, scaledDetections);

          if (data.alert_generated && data.new_alert) {
            handleIncomingLiveAlert(data.new_alert);
          }
        }
      }
    } catch (e) {
      console.error('Frame inference error:', e);
    } finally {
      isLiveInferencing = false;
      if (state.isLiveMonitoring) {
        // Pacing delay eliminates event loop thrashing and allows buttery smooth UI response
        liveFrameTimeoutId = setTimeout(processNextLiveFrame, 150);
      }
    }
  }

  processNextLiveFrame();
}

function drawBoundingBoxesOnCanvas(canvas, detections) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  detections.forEach(det => {
    const [x1, y1, x2, y2] = det.bbox;
    const isViolation = det.class_name.startsWith('no-');
    const color = isViolation ? '#ef4444' : '#10b981';

    // Bounding Box
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    // Label tag
    const text = `${det.class_name} ${det.confidence.toFixed(2)}`;
    ctx.font = 'bold 13px Plus Jakarta Sans, sans-serif';
    const textWidth = ctx.measureText(text).width;
    
    ctx.fillStyle = color;
    ctx.fillRect(x1, Math.max(0, y1 - 22), textWidth + 10, 22);

    ctx.fillStyle = '#ffffff';
    ctx.fillText(text, x1 + 5, Math.max(16, y1 - 6));
  });
}

function handleIncomingLiveAlert(alert) {
  state.liveViolationsTotal++;
  elements.liveViolationsCount.textContent = state.liveViolationsTotal;
  state.unacknowledgedAlertsCount++;
  elements.topAlertCount.textContent = state.unacknowledgedAlertsCount;
  elements.topAlertCount.style.display = 'flex';
  elements.sidebarAlertBadge.textContent = state.unacknowledgedAlertsCount;
  elements.sidebarAlertBadge.style.display = 'inline-block';

  // Update Latest Violation Snapshot
  elements.liveLatestEvidenceContainer.innerHTML = `
    <img src="${alert.evidence_path}" alt="Latest Evidence" style="cursor: pointer;" onclick="openEvidenceModal('${alert.evidence_path}', '${alert.incident_id}', '${alert.violation_category}', '${alert.timestamp}')">
  `;

  // Prepend to live alerts stream
  const alertCard = document.createElement('div');
  alertCard.className = `live-alert-card ${alert.severity.toLowerCase()}`;
  alertCard.innerHTML = `
    <div>
      <strong class="text-red">${alert.violation_category}</strong><br>
      <span class="text-muted" style="font-size: 0.72rem;">${alert.timestamp} • Conf: ${alert.confidence.toFixed(2)}</span>
    </div>
    <span class="${alert.severity === 'CRITICAL' ? 'severity-pill-critical' : 'severity-pill-high'}">${alert.severity}</span>
  `;
  elements.liveAlertsScroll.prepend(alertCard);

  showToast(`Safety Alert: ${alert.violation_category} detected!`, 'error');
  loadIncidents();
}

// ============================================================================
// ALERTS & INCIDENT AUDIT REPOSITORY
// ============================================================================
function setupAlertsModule() {
  elements.btnRefreshAlerts.addEventListener('click', () => {
    loadIncidents();
    showToast('Incidents audit log refreshed.', 'info');
  });

  elements.filterSeverity.addEventListener('change', () => loadIncidents());
  elements.filterStatus.addEventListener('change', () => loadIncidents());
}

async function loadIncidents() {
  try {
    const sev = elements.filterSeverity ? elements.filterSeverity.value : 'ALL';
    const stat = elements.filterStatus ? elements.filterStatus.value : 'ALL';

    const res = await fetch(`/api/alerts?severity=${sev}&status=${stat}`);
    if (!res.ok) return;
    const data = await res.json();

    state.incidentsList = data.incidents || [];
    const stats = data.statistics || {};

    if (elements.alertStatTotal) elements.alertStatTotal.textContent = stats.total || 0;
    if (elements.alertStatCritical) elements.alertStatCritical.textContent = stats.critical || 0;
    if (elements.alertStatHigh) elements.alertStatHigh.textContent = stats.high || 0;
    if (elements.alertStatUnack) elements.alertStatUnack.textContent = stats.unacknowledged || 0;

    const unack = stats.unacknowledged || 0;
    state.unacknowledgedAlertsCount = unack;
    if (elements.topAlertCount) {
      elements.topAlertCount.textContent = unack;
      elements.topAlertCount.style.display = unack > 0 ? 'flex' : 'none';
    }
    if (elements.sidebarAlertBadge) {
      elements.sidebarAlertBadge.textContent = unack;
      elements.sidebarAlertBadge.style.display = unack > 0 ? 'inline-block' : 'none';
    }

    renderIncidentsTable(state.incidentsList);
  } catch (err) {
    console.error('Failed to load incidents:', err);
  }
}

function renderIncidentsTable(incidents) {
  if (!elements.incidentsMasterTableBody) return;
  elements.incidentsMasterTableBody.innerHTML = '';

  if (incidents.length === 0) {
    elements.incidentsMasterTableBody.innerHTML = `
      <tr><td colspan="9" class="text-center text-muted" style="padding: 24px;">No safety incidents recorded matching the active filters.</td></tr>
    `;
    return;
  }

  incidents.forEach(inc => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong class="font-mono">${inc.incident_id}</strong></td>
      <td><span class="${inc.severity === 'CRITICAL' ? 'severity-pill-critical' : (inc.severity === 'HIGH' ? 'severity-pill-high' : 'severity-pill-medium')}">${inc.severity}</span></td>
      <td><span class="tag-violation-red">${inc.violation_category}</span></td>
      <td class="font-mono">${inc.confidence.toFixed(2)}</td>
      <td>${inc.source}</td>
      <td class="font-mono">${inc.timestamp}</td>
      <td class="text-center">
        <img src="${inc.evidence_path}" class="evidence-tiny-thumb" alt="Evidence" onclick="openEvidenceModal('${inc.evidence_path}', '${inc.incident_id}', '${inc.violation_category}', '${inc.timestamp}')">
      </td>
      <td><span class="${inc.status === 'NEW' ? 'status-badge-new' : (inc.status === 'ACKNOWLEDGED' ? 'status-badge-ack' : 'status-badge-dismiss')}">${inc.status}</span></td>
      <td style="text-align: right;">
        ${inc.status === 'NEW' ? `
          <button class="btn btn-sample" style="padding: 2px 8px; font-size: 0.72rem;" onclick="acknowledgeIncident('${inc.incident_id}')">Acknowledge</button>
          <button class="btn btn-action-ghost" style="padding: 2px 8px; font-size: 0.72rem;" onclick="dismissIncident('${inc.incident_id}')">Dismiss</button>
        ` : `<span class="text-muted" style="font-size: 0.75rem;">Archived</span>`}
      </td>
    `;
    elements.incidentsMasterTableBody.appendChild(tr);
  });
}

window.acknowledgeIncident = async function(id) {
  try {
    const res = await fetch(`/api/alerts/${id}/acknowledge`, { method: 'POST' });
    if (res.ok) {
      showToast(`Incident ${id} acknowledged.`, 'success');
      loadIncidents();
    }
  } catch (e) {}
};

window.dismissIncident = async function(id) {
  try {
    const res = await fetch(`/api/alerts/${id}/dismiss`, { method: 'POST' });
    if (res.ok) {
      showToast(`Incident ${id} dismissed.`, 'info');
      loadIncidents();
    }
  } catch (e) {}
};

// ============================================================================
// IMAGE DETECTION MODULE (PHASE 1 PRESERVED)
// ============================================================================
function setupImageDetectionModule() {
  if (!elements.chooseImgBtn) return;

  elements.chooseImgBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    elements.imageInput.click();
  });
  elements.dropZone.addEventListener('click', () => {
    if (!state.selectedImageFile) elements.imageInput.click();
  });

  elements.imageInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) handleImageFile(e.target.files[0]);
  });

  ['dragenter', 'dragover'].forEach(name => {
    elements.dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      elements.dropZone.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach(name => {
    elements.dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      elements.dropZone.classList.remove('dragover');
    });
  });
  elements.dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) handleImageFile(e.dataTransfer.files[0]);
  });

  elements.btnRemoveStaged.addEventListener('click', (e) => {
    e.stopPropagation();
    clearStagedImage();
  });

  elements.loadSampleBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    try {
      const res = await fetch('/assets/sample_worker.jpg');
      const blob = await res.blob();
      handleImageFile(new File([blob], 'sample_worker.jpg', { type: 'image/jpeg' }));
      showToast('Loaded sample PPE worker image.', 'info');
    } catch (e) {}
  });

  elements.btnRunDetection.addEventListener('click', () => runImageDetection());
  elements.btnClearAll.addEventListener('click', () => clearAllImage());
  elements.btnDownloadResult.addEventListener('click', () => {
    if (state.annotatedImageUrl) {
      const a = document.createElement('a');
      a.href = state.annotatedImageUrl;
      a.download = `detection_${Date.now()}.jpg`;
      a.click();
    }
  });

  if (elements.confSlider) {
    elements.confSlider.addEventListener('input', (e) => {
      state.confThreshold = parseFloat(e.target.value);
      if (elements.thresholdValueBadge) {
        elements.thresholdValueBadge.textContent = `${state.confThreshold.toFixed(2)} (${Math.round(state.confThreshold * 100)}%)`;
      }
    });
  }
}

function handleImageFile(file) {
  state.selectedImageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    elements.stagedThumb.src = e.target.result;
    elements.stagedName.textContent = file.name;
    elements.stagedSize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    elements.dropZonePrompt.style.display = 'none';
    elements.stagedPreview.style.display = 'flex';
    elements.resultPlaceholder.style.display = 'none';
    elements.canvasWrapper.style.display = 'flex';
    elements.resultImage.src = e.target.result;
    elements.btnRunDetection.disabled = false;
  };
  reader.readAsDataURL(file);
}

function clearStagedImage() {
  state.selectedImageFile = null;
  elements.imageInput.value = '';
  elements.dropZonePrompt.style.display = 'flex';
  elements.stagedPreview.style.display = 'none';
  elements.btnRunDetection.disabled = true;
  if (!state.annotatedImageUrl) {
    elements.canvasWrapper.style.display = 'none';
    elements.resultPlaceholder.style.display = 'flex';
  }
}

function clearAllImage() {
  clearStagedImage();
  state.annotatedImageUrl = null;
  elements.canvasWrapper.style.display = 'none';
  elements.resultPlaceholder.style.display = 'flex';
  elements.resultImage.src = '';
  elements.inferenceTimerBadge.style.display = 'none';
  elements.btnDownloadResult.disabled = true;
  elements.detectionTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted" style="padding:20px;">Awaiting model inference...</td></tr>';
  elements.summaryTotalCount.textContent = '0';
  elements.summaryUniqueClasses.textContent = '0';
  elements.summaryPeakConf.textContent = '0.00';
  showToast('Image workspace reset.', 'info');
}

async function runImageDetection() {
  if (!state.selectedImageFile || state.isImageProcessing) return;
  state.isImageProcessing = true;
  elements.btnRunDetection.disabled = true;
  elements.processingOverlay.style.display = 'flex';

  const formData = new FormData();
  formData.append('file', state.selectedImageFile);

  try {
    const res = await fetch(`/api/detect/image?confidence=${state.confThreshold}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Inference request failed');
    const data = await res.json();

    state.annotatedImageUrl = data.annotated_image_url;
    elements.resultImage.src = `${data.annotated_image_url}?t=${Date.now()}`;
    elements.inferenceTimerBadge.style.display = 'flex';
    elements.inferenceTimeVal.textContent = `${data.inference_time}s`;

    // Render table
    elements.detectionTableBody.innerHTML = '';
    (data.detections || []).forEach((d, idx) => {
      const isViol = d.class_name.startsWith('no-');
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${idx + 1}</strong></td>
        <td><span class="${isViol ? 'tag-violation-red' : 'tag-helmet'}">${d.class_name}</span></td>
        <td class="conf-cell">${d.confidence.toFixed(2)}</td>
      `;
      elements.detectionTableBody.appendChild(tr);
    });

    elements.summaryTotalCount.textContent = data.total_detections;
    elements.summaryUniqueClasses.textContent = data.unique_classes_count;
    elements.summaryPeakConf.textContent = data.highest_confidence.toFixed(2);
    elements.btnDownloadResult.disabled = false;

    showToast(`Detection complete! Found ${data.total_detections} item(s).`, 'success');
  } catch (err) {
    showToast('Inference error: ' + err.message, 'error');
  } finally {
    state.isImageProcessing = false;
    elements.processingOverlay.style.display = 'none';
    elements.btnRunDetection.disabled = false;
  }
}

// ============================================================================
// PHASE 3: ADVANCED ANALYTICS MODULE
// ============================================================================
function setupAnalyticsModule() {
  if (!elements.btnRefreshAnalytics) return;

  // Range pills
  document.querySelectorAll('.range-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.range-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const range = pill.getAttribute('data-range');
      applyDateRangePreset(range);
      loadAnalytics();
    });
  });

  // Apply filters button
  elements.btnApplyAnalyticsFilters.addEventListener('click', () => {
    loadAnalytics();
  });

  // Reset filters button
  elements.btnResetAnalyticsFilters.addEventListener('click', () => {
    elements.analyticsCategory.value = 'ALL';
    elements.analyticsSeverity.value = 'ALL';
    elements.analyticsSource.value = 'ALL';
    // Reset to 30d
    document.querySelectorAll('.range-pill').forEach(p => p.classList.remove('active'));
    const p30 = document.querySelector('.range-pill[data-range="30d"]');
    if (p30) p30.classList.add('active');
    applyDateRangePreset('30d');
    loadAnalytics();
    showToast('Analytics filters reset to default (30 Days).', 'info');
  });

  // Refresh button
  elements.btnRefreshAnalytics.addEventListener('click', () => {
    loadAnalytics();
    showToast('Analytics data refreshed.', 'info');
  });

  // Initialize default 30-day date preset
  applyDateRangePreset('30d');
}

function applyDateRangePreset(range) {
  const today = new Date();
  const pad = n => String(n).padStart(2, '0');
  const format = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

  if (range === 'today') {
    elements.analyticsStartDate.value = format(today);
    elements.analyticsEndDate.value = format(today);
  } else if (range === '7d') {
    const past = new Date(today);
    past.setDate(past.getDate() - 7);
    elements.analyticsStartDate.value = format(past);
    elements.analyticsEndDate.value = format(today);
  } else if (range === '30d') {
    const past = new Date(today);
    past.setDate(past.getDate() - 30);
    elements.analyticsStartDate.value = format(past);
    elements.analyticsEndDate.value = format(today);
  } else if (range === '90d') {
    const past = new Date(today);
    past.setDate(past.getDate() - 90);
    elements.analyticsStartDate.value = format(past);
    elements.analyticsEndDate.value = format(today);
  } else if (range === 'all') {
    elements.analyticsStartDate.value = '';
    elements.analyticsEndDate.value = '';
  }
}

async function loadAnalytics() {
  try {
    const startDate = elements.analyticsStartDate ? elements.analyticsStartDate.value : '';
    const endDate = elements.analyticsEndDate ? elements.analyticsEndDate.value : '';
    const category = elements.analyticsCategory ? elements.analyticsCategory.value : 'ALL';
    const severity = elements.analyticsSeverity ? elements.analyticsSeverity.value : 'ALL';
    const source = elements.analyticsSource ? elements.analyticsSource.value : 'ALL';

    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (category !== 'ALL') params.append('category', category);
    if (severity !== 'ALL') params.append('severity', severity);
    if (source !== 'ALL') params.append('source', source);

    const queryStr = params.toString() ? `?${params.toString()}` : '';

    // Fetch all analytics datasets concurrently
    const [overviewRes, violationsRes, trendsRes, severityRes, sourcesRes] = await Promise.all([
      fetch(`/api/analytics/overview${queryStr}`),
      fetch(`/api/analytics/violations${queryStr}`),
      fetch(`/api/analytics/trends${queryStr}`),
      fetch(`/api/analytics/severity${queryStr}`),
      fetch(`/api/analytics/sources${queryStr}`)
    ]);

    if (overviewRes.ok) {
      const overview = await overviewRes.json();
      updateAnalyticsKpis(overview.analytics || overview);
    }

    if (violationsRes.ok) {
      const violationsData = await violationsRes.json();
      renderViolationsByCategoryChart(violationsData.violations || violationsData.categories || []);
    }

    if (trendsRes.ok) {
      const trendsData = await trendsRes.json();
      renderIncidentsTrendChart(trendsData.trends || trendsData.timeline || []);
    }

    if (severityRes.ok) {
      const severityData = await severityRes.json();
      const rawSev = severityData.severity_distribution || severityData.severities || {};
      const sevList = Array.isArray(rawSev) ? rawSev : Object.entries(rawSev).map(([k, v]) => ({ severity: k, count: v }));
      renderSeverityDistChart(sevList);
    }

    if (sourcesRes.ok) {
      const sourcesData = await sourcesRes.json();
      const rawSrc = sourcesData.source_distribution || sourcesData.sources || {};
      const srcList = Array.isArray(rawSrc) ? rawSrc : Object.entries(rawSrc).map(([k, v]) => ({ source: k, count: v }));
      renderSourceDistChart(srcList);
    }
  } catch (err) {
    console.error('Failed to load analytics:', err);
  }
}

function updateAnalyticsKpis(data) {
  if (elements.kpiTotalIncidents) elements.kpiTotalIncidents.textContent = data.total_incidents || 0;
  if (elements.kpiTotalViolations) elements.kpiTotalViolations.textContent = data.total_violations || data.violation_detections || 0;
  if (elements.kpiCompliantDetections) elements.kpiCompliantDetections.textContent = data.compliant_detections || 0;
  if (elements.kpiCriticalIncidents) elements.kpiCriticalIncidents.textContent = data.critical_incidents || 0;
  if (elements.kpiResolvedIncidents) elements.kpiResolvedIncidents.textContent = data.resolved_incidents || 0;

  // Compliance Rate Badge & Label
  if (elements.kpiComplianceRate && elements.kpiComplianceBadge) {
    const pct = (data.compliance_percentage !== undefined && data.compliance_percentage !== null) 
      ? data.compliance_percentage 
      : (typeof data.compliance_rate === 'number' ? data.compliance_rate : null);

    if (pct !== null) {
      elements.kpiComplianceRate.textContent = `${pct.toFixed(1)}%`;
      if (pct >= 85) {
        elements.kpiComplianceBadge.className = 'compliance-badge badge-safe';
        elements.kpiComplianceBadge.textContent = 'Compliant';
      } else if (pct >= 70) {
        elements.kpiComplianceBadge.className = 'compliance-badge badge-warning';
        elements.kpiComplianceBadge.textContent = 'Attention';
      } else {
        elements.kpiComplianceBadge.className = 'compliance-badge badge-danger';
        elements.kpiComplianceBadge.textContent = 'Violations High';
      }
    } else {
      elements.kpiComplianceRate.textContent = data.compliance_rate || '--%';
      elements.kpiComplianceBadge.className = 'compliance-badge badge-warning';
      elements.kpiComplianceBadge.textContent = 'No Data';
    }
  }
}

function renderViolationsByCategoryChart(categories) {
  const canvas = document.getElementById('chartViolationsByCategory');
  if (!canvas) return;
  if (state.charts.violations) state.charts.violations.destroy();

  const labels = categories.map(c => c.category);
  const counts = categories.map(c => c.count);
  const colors = labels.map(label => {
    const l = label.toLowerCase();
    if (l.includes('helmet')) return '#ef4444';
    if (l.includes('vest')) return '#f97316';
    if (l.includes('gloves')) return '#3b82f6';
    if (l.includes('goggles')) return '#8b5cf6';
    if (l.includes('boots')) return '#10b981';
    return '#6366f1';
  });

  state.charts.violations = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Helmet', 'Vest', 'Gloves', 'Goggles', 'Boots'],
      datasets: [{
        label: 'Violations Logged',
        data: counts.length ? counts : [0, 0, 0, 0, 0],
        backgroundColor: colors.length ? colors : ['#ef4444', '#f97316', '#3b82f6', '#8b5cf6', '#10b981'],
        borderRadius: 6,
        barThickness: 28
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { family: 'Plus Jakarta Sans', size: 12 },
          bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
          padding: 10,
          cornerRadius: 6
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0, font: { family: 'JetBrains Mono', size: 11 } },
          grid: { color: '#f1f5f9' }
        },
        x: {
          ticks: { font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' } },
          grid: { display: false }
        }
      }
    }
  });
}

function renderIncidentsTrendChart(timeline) {
  const canvas = document.getElementById('chartIncidentsTrend');
  if (!canvas) return;
  if (state.charts.trends) state.charts.trends.destroy();

  const labels = timeline.map(t => t.date);
  const counts = timeline.map(t => t.count);

  state.charts.trends = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels.length ? labels : ['No Activity'],
      datasets: [{
        label: 'Violations Detected',
        data: counts.length ? counts : [0],
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.08)',
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#4f46e5',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { family: 'Plus Jakarta Sans', size: 12 },
          bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
          padding: 10,
          cornerRadius: 6
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0, font: { family: 'JetBrains Mono', size: 11 } },
          grid: { color: '#f1f5f9' }
        },
        x: {
          ticks: { font: { family: 'Plus Jakarta Sans', size: 10 } },
          grid: { color: '#f8fafc' }
        }
      }
    }
  });
}

function renderSeverityDistChart(severities) {
  const canvas = document.getElementById('chartSeverityDist');
  if (!canvas) return;
  if (state.charts.severity) state.charts.severity.destroy();

  const labels = severities.map(s => s.severity);
  const counts = severities.map(s => s.count);
  const colorMap = {
    'CRITICAL': '#ef4444',
    'HIGH': '#f97316',
    'MEDIUM': '#f59e0b',
    'LOW': '#3b82f6'
  };
  const colors = labels.map(l => colorMap[l.toUpperCase()] || '#94a3b8');

  state.charts.severity = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels.length ? labels : ['No Incidents'],
      datasets: [{
        data: counts.length ? counts : [1],
        backgroundColor: counts.length ? colors : ['#e2e8f0'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
            padding: 12
          }
        }
      }
    }
  });
}

function renderSourceDistChart(sources) {
  const canvas = document.getElementById('chartSourceDist');
  if (!canvas) return;
  if (state.charts.sources) state.charts.sources.destroy();

  const labels = sources.map(s => s.source);
  const counts = sources.map(s => s.count);
  const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981'];

  state.charts.sources = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: labels.length ? labels : ['No Sources'],
      datasets: [{
        data: counts.length ? counts : [1],
        backgroundColor: counts.length ? colors.slice(0, labels.length) : ['#e2e8f0'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            boxWidth: 12,
            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
            padding: 12
          }
        }
      }
    }
  });
}

// ============================================================================
// PHASE 3: INCIDENT HISTORY & RESOLUTION MANAGEMENT MODULE
// ============================================================================
let incidentSearchDebounceTimer = null;

function setupIncidentHistoryModule() {
  if (!elements.incidentSearchInput) return;

  // Search input with debounce
  elements.incidentSearchInput.addEventListener('input', () => {
    clearTimeout(incidentSearchDebounceTimer);
    incidentSearchDebounceTimer = setTimeout(() => {
      state.incidentHistoryFilter.page = 1;
      loadIncidentAuditTable();
    }, 350);
  });

  // Filter dropdowns
  elements.incidentFilterCategory.addEventListener('change', () => {
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });
  elements.incidentFilterSeverity.addEventListener('change', () => {
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });
  elements.incidentFilterSource.addEventListener('change', () => {
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });
  elements.incidentFilterStatus.addEventListener('change', () => {
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });

  // Date filters apply & reset
  elements.btnFilterIncidents.addEventListener('click', () => {
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });

  elements.btnResetIncidentFilters.addEventListener('click', () => {
    elements.incidentSearchInput.value = '';
    elements.incidentFilterCategory.value = 'ALL';
    elements.incidentFilterSeverity.value = 'ALL';
    elements.incidentFilterSource.value = 'ALL';
    elements.incidentFilterStatus.value = 'ALL';
    elements.incidentStartDate.value = '';
    elements.incidentEndDate.value = '';
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
    showToast('Incident filters reset.', 'info');
  });

  // Page size selector
  elements.incidentPageSize.addEventListener('change', () => {
    state.incidentHistoryFilter.limit = parseInt(elements.incidentPageSize.value);
    state.incidentHistoryFilter.page = 1;
    loadIncidentAuditTable();
  });

  // Pagination buttons
  elements.btnPrevPage.addEventListener('click', () => {
    if (state.incidentHistoryFilter.page > 1) {
      state.incidentHistoryFilter.page--;
      loadIncidentAuditTable();
    }
  });

  elements.btnNextPage.addEventListener('click', () => {
    if (state.incidentHistoryFilter.page < state.incidentHistoryFilter.totalPages) {
      state.incidentHistoryFilter.page++;
      loadIncidentAuditTable();
    }
  });

  // CSV Export from Incident History Toolbar
  elements.btnExportIncidentsCsv.addEventListener('click', () => {
    exportFilteredIncidentsCsv();
  });

  // Modal actions
  elements.incidentDetailCloseBtn.addEventListener('click', closeIncidentDetailModal);
  elements.modalIncidentCancelBtn.addEventListener('click', closeIncidentDetailModal);
  elements.modalIncidentSaveBtn.addEventListener('click', saveIncidentResolution);
}

async function loadIncidentAuditTable() {
  if (!elements.incidentsAuditTableBody) return;

  const f = state.incidentHistoryFilter;
  const search = elements.incidentSearchInput ? elements.incidentSearchInput.value.trim() : '';
  const category = elements.incidentFilterCategory ? elements.incidentFilterCategory.value : 'ALL';
  const severity = elements.incidentFilterSeverity ? elements.incidentFilterSeverity.value : 'ALL';
  const source = elements.incidentFilterSource ? elements.incidentFilterSource.value : 'ALL';
  const status = elements.incidentFilterStatus ? elements.incidentFilterStatus.value : 'ALL';
  const startDate = elements.incidentStartDate ? elements.incidentStartDate.value : '';
  const endDate = elements.incidentEndDate ? elements.incidentEndDate.value : '';

  const offset = (f.page - 1) * f.limit;
  const params = new URLSearchParams({
    limit: f.limit,
    offset: offset
  });

  if (search) params.append('search', search);
  if (category !== 'ALL') params.append('category', category);
  if (severity !== 'ALL') params.append('severity', severity);
  if (source !== 'ALL') params.append('source', source);
  if (status !== 'ALL') params.append('status', status);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  try {
    const res = await fetch(`/api/incidents?${params.toString()}`);
    if (!res.ok) return;
    const data = await res.json();

    const incidents = data.incidents || [];
    const total = data.total || 0;
    f.totalRecords = total;
    f.totalPages = Math.max(1, Math.ceil(total / f.limit));

    // Update Pagination Display
    const startIdx = total === 0 ? 0 : offset + 1;
    const endIdx = Math.min(offset + f.limit, total);
    if (elements.incidentTableCountSummary) {
      elements.incidentTableCountSummary.textContent = `Showing ${startIdx}-${endIdx} of ${total} records`;
    }
    if (elements.pageIndicator) {
      elements.pageIndicator.textContent = `Page ${f.page} of ${f.totalPages}`;
    }
    if (elements.btnPrevPage) elements.btnPrevPage.disabled = f.page <= 1;
    if (elements.btnNextPage) elements.btnNextPage.disabled = f.page >= f.totalPages;

    renderAuditTableRows(incidents);
  } catch (err) {
    console.error('Error loading incident audit table:', err);
  }
}

function renderAuditTableRows(incidents) {
  elements.incidentsAuditTableBody.innerHTML = '';

  if (incidents.length === 0) {
    elements.incidentsAuditTableBody.innerHTML = `
      <tr><td colspan="9" class="text-center text-muted" style="padding: 30px;">No incident records matching the selected search and filter criteria.</td></tr>
    `;
    return;
  }

  incidents.forEach(inc => {
    const tr = document.createElement('tr');
    const isCritical = inc.severity === 'CRITICAL';
    const isHigh = inc.severity === 'HIGH';
    const sevPillClass = isCritical ? 'severity-pill-critical' : (isHigh ? 'severity-pill-high' : 'severity-pill-medium');
    
    let statusBadgeClass = 'status-badge-new';
    if (inc.status === 'ACKNOWLEDGED') statusBadgeClass = 'status-badge-ack';
    if (inc.status === 'RESOLVED') statusBadgeClass = 'status-badge-resolved';

    tr.innerHTML = `
      <td><strong class="font-mono text-purple">${inc.incident_id}</strong></td>
      <td><span class="tag-violation-red">${inc.violation_category}</span></td>
      <td class="font-mono">${(inc.confidence * 100).toFixed(0)}%</td>
      <td><span class="${sevPillClass}">${inc.severity}</span></td>
      <td>${formatSourceLabel(inc.source)}</td>
      <td class="font-mono text-muted">${inc.timestamp}</td>
      <td><span class="${statusBadgeClass}">${inc.status}</span></td>
      <td class="text-center">
        <img src="${inc.evidence_path}" class="evidence-tiny-thumb" alt="Evidence" onclick="openIncidentDetailModal('${inc.incident_id}')">
      </td>
      <td style="text-align: right;">
        <button class="btn btn-outline btn-sm" onclick="openIncidentDetailModal('${inc.incident_id}')">
          <i class="fa-solid fa-file-pen"></i> Resolve
        </button>
      </td>
    `;
    elements.incidentsAuditTableBody.appendChild(tr);
  });
}

function formatSourceLabel(source) {
  if (source === 'image_upload') return '<i class="fa-regular fa-image"></i> Image';
  if (source === 'video_detection') return '<i class="fa-solid fa-video"></i> Video';
  if (source === 'live_webcam') return '<i class="fa-solid fa-tower-broadcast"></i> Webcam';
  if (source === 'cctv_stream') return '<i class="fa-solid fa-camera"></i> CCTV';
  return source;
}

window.openIncidentDetailModal = async function(incidentId) {
  try {
    const res = await fetch(`/api/incidents/${incidentId}`);
    if (!res.ok) throw new Error('Incident not found');
    const data = await res.json();
    const inc = data.incident;

    state.activeIncidentForModal = inc;

    elements.modalIncidentIdBadge.textContent = inc.incident_id;
    elements.modalIncidentEvidenceImg.src = inc.evidence_path;
    elements.modalIncidentDownloadBtn.href = inc.evidence_path;
    elements.modalIncidentViolation.textContent = inc.violation_category;
    elements.modalIncidentSeverity.textContent = inc.severity;
    elements.modalIncidentSeverity.className = `severity-badge ${inc.severity === 'CRITICAL' ? 'severity-pill-critical' : 'severity-pill-high'}`;
    elements.modalIncidentConfidence.textContent = `${(inc.confidence * 100).toFixed(1)}%`;
    elements.modalIncidentSource.textContent = inc.source;
    elements.modalIncidentTimestamp.textContent = inc.timestamp;
    elements.modalResolutionStatus.value = inc.status;
    elements.modalResolutionNotes.value = inc.resolution_notes || '';

    if (inc.resolved_at) {
      elements.modalResolvedMeta.style.display = 'block';
      elements.modalResolvedTime.textContent = inc.resolved_at;
    } else {
      elements.modalResolvedMeta.style.display = 'none';
    }

    elements.incidentDetailModal.style.display = 'flex';
  } catch (err) {
    showToast('Failed to load incident detail: ' + err.message, 'error');
  }
};

function closeIncidentDetailModal() {
  if (elements.incidentDetailModal) {
    elements.incidentDetailModal.style.display = 'none';
  }
  state.activeIncidentForModal = null;
}

async function saveIncidentResolution() {
  if (!state.activeIncidentForModal) return;
  const incId = state.activeIncidentForModal.incident_id;
  const newStatus = elements.modalResolutionStatus.value;
  const notes = elements.modalResolutionNotes.value.trim();

  elements.modalIncidentSaveBtn.disabled = true;
  elements.modalIncidentSaveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const res = await fetch(`/api/incidents/${incId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: newStatus,
        resolution_notes: notes
      })
    });

    if (!res.ok) throw new Error('Status update failed');
    const data = await res.json();

    showToast(`Incident ${incId} updated to ${newStatus}.`, 'success');
    closeIncidentDetailModal();
    loadIncidentAuditTable();
    loadIncidents(); // updates alert badges
  } catch (err) {
    showToast('Failed to update incident: ' + err.message, 'error');
  } finally {
    elements.modalIncidentSaveBtn.disabled = false;
    elements.modalIncidentSaveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Save Status &amp; Notes';
  }
}

async function exportFilteredIncidentsCsv() {
  const category = elements.incidentFilterCategory ? elements.incidentFilterCategory.value : 'ALL';
  const severity = elements.incidentFilterSeverity ? elements.incidentFilterSeverity.value : 'ALL';
  const source = elements.incidentFilterSource ? elements.incidentFilterSource.value : 'ALL';
  const startDate = elements.incidentStartDate ? elements.incidentStartDate.value : null;
  const endDate = elements.incidentEndDate ? elements.incidentEndDate.value : null;

  try {
    showToast('Generating CSV export...', 'info');
    const res = await fetch('/api/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report_type: 'custom',
        title: 'Industrial Safety Incidents Audit Log',
        format: 'csv',
        start_date: startDate || null,
        end_date: endDate || null,
        severity: severity !== 'ALL' ? severity : null,
        violation_category: category !== 'ALL' ? category : null,
        source: source !== 'ALL' ? source : null
      })
    });

    if (!res.ok) throw new Error('Export failed');
    const data = await res.json();
    if (data.download_url) {
      window.location.href = data.download_url;
      showToast('CSV downloaded successfully.', 'success');
      loadReportsHistory();
    }
  } catch (err) {
    showToast('CSV Export failed: ' + err.message, 'error');
  }
}

// ============================================================================
// PHASE 3: PROFESSIONAL SAFETY REPORTS MODULE
// ============================================================================
function setupReportsModule() {
  if (!elements.reportGenerationForm) return;

  // Format selection toggle cards
  elements.formatCardPdf.addEventListener('click', () => {
    state.selectedReportFormat = 'pdf';
    elements.formatCardPdf.classList.add('active');
    elements.formatCardCsv.classList.remove('active');
  });

  elements.formatCardCsv.addEventListener('click', () => {
    state.selectedReportFormat = 'csv';
    elements.formatCardCsv.classList.add('active');
    elements.formatCardPdf.classList.remove('active');
  });

  // Report type presets date handler
  if (elements.reportTypeSelect) {
    const updateReportDates = () => {
      const type = elements.reportTypeSelect.value;
      const today = new Date();
      const pad = n => String(n).padStart(2, '0');
      const format = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

      if (type === 'daily') {
        elements.reportStartDate.value = format(today);
        elements.reportEndDate.value = format(today);
      } else if (type === 'weekly') {
        const past = new Date(today);
        past.setDate(past.getDate() - 7);
        elements.reportStartDate.value = format(past);
        elements.reportEndDate.value = format(today);
      } else if (type === 'monthly') {
        const past = new Date(today);
        past.setDate(past.getDate() - 30);
        elements.reportStartDate.value = format(past);
        elements.reportEndDate.value = format(today);
      } else if (type === 'custom') {
        // Leave existing values or let user pick freely
      }
    };
    elements.reportTypeSelect.addEventListener('change', updateReportDates);
    // Initialize default weekly dates
    updateReportDates();
  }

  // Report Form submit
  elements.reportGenerationForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await generateCustomReport();
  });

  // Refresh reports history button
  elements.btnRefreshReportsHistory.addEventListener('click', () => {
    loadReportsHistory();
    showToast('Reports history refreshed.', 'info');
  });
}

async function generateCustomReport() {
  const reportType = elements.reportTypeSelect.value;
  const format = state.selectedReportFormat;
  const startDate = elements.reportStartDate.value || null;
  const endDate = elements.reportEndDate.value || null;
  const severity = elements.reportSeveritySelect.value !== 'ALL' ? elements.reportSeveritySelect.value : null;
  const category = elements.reportCategorySelect.value !== 'ALL' ? elements.reportCategorySelect.value : null;

  elements.btnGenerateReport.disabled = true;
  elements.btnGenerateReport.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Report...';

  try {
    const res = await fetch('/api/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        report_type: reportType,
        title: `Industrial Safety Audit Report — ${reportType.toUpperCase()}`,
        format: format,
        start_date: startDate,
        end_date: endDate,
        severity: severity,
        violation_category: category
      })
    });

    if (!res.ok) throw new Error('Report generation error');
    const data = await res.json();

    showToast(`Generated ${format.toUpperCase()} report with ${data.records_count} record(s).`, 'success');
    
    // Automatically trigger file download
    if (data.download_url) {
      const a = document.createElement('a');
      a.href = data.download_url;
      a.download = '';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }

    loadReportsHistory();
  } catch (err) {
    showToast('Failed to generate report: ' + err.message, 'error');
  } finally {
    elements.btnGenerateReport.disabled = false;
    elements.btnGenerateReport.innerHTML = '<i class="fa-solid fa-file-arrow-down"></i> <span>Generate &amp; Download Report</span>';
  }
}

async function loadReportsHistory() {
  if (!elements.reportsHistoryTableBody) return;

  try {
    const res = await fetch('/api/reports/summary');
    if (!res.ok) return;
    const data = await res.json();
    const reports = data.recent_reports || [];

    elements.reportsHistoryTableBody.innerHTML = '';
    if (reports.length === 0) {
      elements.reportsHistoryTableBody.innerHTML = `
        <tr><td colspan="7" class="text-center text-muted" style="padding: 24px;">No safety reports generated yet. Use the form on the left to export PDF or CSV reports.</td></tr>
      `;
      return;
    }

    reports.forEach(rpt => {
      const isPdf = rpt.format === 'pdf';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong class="font-mono text-purple">${rpt.report_id}</strong></td>
        <td><strong>${rpt.report_type.toUpperCase()}</strong></td>
        <td><span class="${isPdf ? 'tag-violation-red' : 'tag-helmet'}">${rpt.format.toUpperCase()}</span></td>
        <td class="font-mono">${rpt.total_incidents}</td>
        <td class="font-mono text-muted" style="font-size: 0.75rem;">${rpt.start_date} &rarr; ${rpt.end_date}</td>
        <td class="font-mono text-muted" style="font-size: 0.75rem;">${rpt.generated_at}</td>
        <td style="text-align: right;">
          <a href="/api/reports/download/${rpt.report_id}" class="btn btn-primary btn-sm" download style="text-decoration: none;">
            <i class="fa-solid fa-download"></i> Download
          </a>
        </td>
      `;
      elements.reportsHistoryTableBody.appendChild(tr);
    });
  } catch (err) {
    console.error('Failed to load reports history:', err);
  }
}

// ============================================================================
// PHASE 3: SYSTEM SETTINGS & DIAGNOSTICS MODULE
// ============================================================================
function setupSettingsModule() {
  if (!elements.btnSaveSystemSettings) return;

  // Slider badge update
  elements.settingsConfThreshold.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    elements.settingsConfBadge.textContent = `${val.toFixed(2)} (${Math.round(val * 100)}%)`;
  });

  // Save Settings button
  elements.btnSaveSystemSettings.addEventListener('click', saveSystemSettings);

  // Refresh Diagnostics button
  elements.btnRefreshDiagnostics.addEventListener('click', () => {
    loadStorageDiagnostics();
    showToast('Diagnostics refreshed.', 'info');
  });
}

async function loadSystemSettings() {
  try {
    const res = await fetch('/api/settings');
    if (!res.ok) return;
    const data = await res.json();
    const s = data.settings || {};

    if (elements.settingsConfThreshold && s.model_confidence_threshold) {
      const conf = parseFloat(s.model_confidence_threshold);
      elements.settingsConfThreshold.value = conf;
      elements.settingsConfBadge.textContent = `${conf.toFixed(2)} (${Math.round(conf * 100)}%)`;
      state.confThreshold = conf;
    }

    if (elements.settingsFrameStride && s.video_frame_stride) {
      elements.settingsFrameStride.value = s.video_frame_stride;
    }

    if (elements.settingsCooldown && s.alert_cooldown_seconds) {
      elements.settingsCooldown.value = s.alert_cooldown_seconds;
    }

    const minSev = s.min_severity_alert || s.min_severity_level;
    if (elements.settingsMinSeverity && minSev) {
      elements.settingsMinSeverity.value = minSev;
    }

    if (elements.settingsFacilityName && s.facility_name) {
      elements.settingsFacilityName.value = s.facility_name;
    }

    loadStorageDiagnostics(data);
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

async function saveSystemSettings() {
  const conf = parseFloat(elements.settingsConfThreshold.value);
  const stride = parseInt(elements.settingsFrameStride.value);
  const cooldown = parseInt(elements.settingsCooldown.value);
  const minSev = elements.settingsMinSeverity.value;
  const facility = elements.settingsFacilityName.value.trim();

  elements.btnSaveSystemSettings.disabled = true;
  elements.btnSaveSystemSettings.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_confidence_threshold: conf,
        video_frame_stride: stride,
        alert_cooldown_seconds: cooldown,
        min_severity_alert: minSev,
        min_severity_level: minSev,
        facility_name: facility
      })
    });

    if (!res.ok) throw new Error('Settings save failed');
    state.confThreshold = conf;
    showToast('Surveillance settings successfully saved to SQLite repository.', 'success');
  } catch (err) {
    showToast('Failed to save settings: ' + err.message, 'error');
  } finally {
    elements.btnSaveSystemSettings.disabled = false;
    elements.btnSaveSystemSettings.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Settings';
  }
}

async function loadStorageDiagnostics(existingData = null) {
  try {
    const data = existingData || await (await fetch('/api/settings')).json();
    if (!data) return;

    if (elements.diagDbSize) {
      const kb = ((data.database_size_bytes || 0) / 1024).toFixed(1);
      elements.diagDbSize.textContent = `${kb} KB`;
    }

    if (elements.diagStorageSize) {
      const mb = ((data.evidence_storage_bytes || 0) / (1024 * 1024)).toFixed(2);
      elements.diagStorageSize.textContent = `${mb} MB`;
    }

    if (elements.diagTotalIncidents) {
      elements.diagTotalIncidents.textContent = data.total_logged_incidents || 0;
    }

    const counts = data.evidence_counts || {};
    const sys = data.system_info || {};
    if (elements.diagBackendStatus) {
      elements.diagBackendStatus.textContent = sys.backend_status || 'Online (FastAPI 0.115)';
    }
    if (elements.diagDbStatus) {
      elements.diagDbStatus.textContent = sys.database_status || 'Connected (SQLite WAL)';
    }
    if (elements.diagTotalVideos) {
      elements.diagTotalVideos.textContent = counts.videos || 0;
    }
    if (elements.diagTotalReports) {
      elements.diagTotalReports.textContent = counts.reports || 0;
    }
  } catch (err) {
    console.error('Failed to load storage diagnostics:', err);
  }
}


function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info');
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
