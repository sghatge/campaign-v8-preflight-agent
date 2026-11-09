// Demo UI using verified Milestone 1 synthetic scenario results.
// This front-end mirrors engine outcomes for demonstration; the Python engine remains the source of truth for checks.

const scenarios = [
  {
    id: 'synthetic-cmp-pass-001', name: 'Spring Reactivation (PASS)', verdict: 'PASS',
    summary: 'Overall verdict: PASS. All configured checks passed; named approval may still be required by policy.',
    meta: 'Email · Europe/London · target 12,500 · baseline 11,800 · proof approved',
    checks: [
      {id:'PF-01',name:'Audience count present',sev:'required',result:'pass',obs:'{"target_count":12500}',thr:'{"target_count_gt":0}',why:'Target audience contains 12500 contacts.'},
      {id:'PF-02',name:'Audience drift vs baseline',sev:'warning',result:'pass',obs:'{"target_count":12500,"baseline_count":11800,"drift_abs_pct":5.93}',thr:'{"risk_abs_pct":30,"fail_abs_pct":50}',why:'Audience drift is 5.9%, within tolerance.'},
      {id:'PF-03',name:'Suppression/consent coverage',sev:'required',result:'pass',obs:'{"suppression_applied":true,"consent_filter_applied":true}',thr:'required true',why:'Suppression and consent filters are applied.'},
      {id:'PF-04',name:'Seed/proof status',sev:'warning',result:'pass',obs:'{"proof_status":"approved","seed_list_present":true}',thr:'approved or waived',why:'Proof is approved. Seed list is present.'},
      {id:'PF-05',name:'Personalization fields available',sev:'required',result:'pass',obs:'{"required":["first_name"],"missing_mappings":[]}',thr:'no missing mappings',why:'Required personalization mappings are present.'},
      {id:'PF-06',name:'Link/mirror sanity',sev:'required',result:'pass',obs:'{"unsubscribe_present":true,"mirror_present":true}',thr:'required present',why:'Unsubscribe and mirror indicators are present.'},
      {id:'PF-07',name:'Schedule/timezone sanity',sev:'required',result:'pass',obs:'{"send_at":"2026-11-15T09:00:00Z","timezone":"Europe/London"}',thr:'present',why:'Schedule and timezone are present (format sanity check passed).'},
      {id:'PF-08',name:'Workflow/dependency readiness',sev:'required',result:'pass',obs:'{"status":"ready","dependencies_ok":true,"pending_approvals":0}',thr:'deps ok, 0 pending',why:'Workflow dependencies and approvals are ready.'}
    ]
  },
  {
    id: 'synthetic-cmp-risk-002', name: 'Winback (RISK: audience drift)', verdict: 'RISK',
    summary: 'Overall verdict: RISK. Risk/warning checks: PF-02. Review warnings before approval.',
    meta: 'Email · Europe/Paris · target 6,200 · baseline 11,000 · proof approved',
    checks: [
      {id:'PF-01',name:'Audience count present',sev:'required',result:'pass',obs:'{"target_count":6200}',thr:'{"target_count_gt":0}',why:'Target audience contains 6200 contacts.'},
      {id:'PF-02',name:'Audience drift vs baseline',sev:'warning',result:'risk',obs:'{"target_count":6200,"baseline_count":11000,"drift_abs_pct":43.64}',thr:'{"risk_abs_pct":30,"fail_abs_pct":50}',why:'Audience drift is 43.6% (>= 30%); review before approval.'},
      {id:'PF-03',name:'Suppression/consent coverage',sev:'required',result:'pass',obs:'{"suppression_applied":true,"consent_filter_applied":true}',thr:'required true',why:'Suppression and consent filters are applied.'},
      {id:'PF-04',name:'Seed/proof status',sev:'warning',result:'pass',obs:'{"proof_status":"approved","seed_list_present":true}',thr:'approved or waived',why:'Proof is approved. Seed list is present.'},
      {id:'PF-05',name:'Personalization fields available',sev:'required',result:'pass',obs:'{"required":["first_name","city"],"missing_mappings":[]}',thr:'no missing mappings',why:'Required personalization mappings are present.'},
      {id:'PF-06',name:'Link/mirror sanity',sev:'required',result:'pass',obs:'{"unsubscribe_present":true,"mirror_present":true}',thr:'required present',why:'Unsubscribe and mirror indicators are present.'},
      {id:'PF-07',name:'Schedule/timezone sanity',sev:'required',result:'pass',obs:'{"send_at":"2026-11-16T08:30:00Z","timezone":"Europe/Paris"}',thr:'present',why:'Schedule and timezone are present (format sanity check passed).'},
      {id:'PF-08',name:'Workflow/dependency readiness',sev:'required',result:'pass',obs:'{"status":"ready","dependencies_ok":true,"pending_approvals":0}',thr:'deps ok, 0 pending',why:'Workflow dependencies and approvals are ready.'}
    ]
  },
  {
    id: 'synthetic-cmp-fail-003', name: 'Black Friday Teaser (FAIL)', verdict: 'FAIL',
    summary: 'Overall verdict: FAIL. Failed checks: PF-03, PF-05, PF-06, PF-08. Risk/warning checks: PF-04. Release-impacting progression is blocked pending review; override requires a written reason and audit event.',
    meta: 'Email · Europe/Berlin · target 48,000 · suppression missing · proof not sent · workflow pending',
    checks: [
      {id:'PF-01',name:'Audience count present',sev:'required',result:'pass',obs:'{"target_count":48000}',thr:'{"target_count_gt":0}',why:'Target audience contains 48000 contacts.'},
      {id:'PF-02',name:'Audience drift vs baseline',sev:'warning',result:'pass',obs:'{"target_count":48000,"baseline_count":47000,"drift_abs_pct":2.13}',thr:'{"risk_abs_pct":30,"fail_abs_pct":50}',why:'Audience drift is 2.1%, within tolerance.'},
      {id:'PF-03',name:'Suppression/consent coverage',sev:'required',result:'fail',obs:'{"suppression_applied":false,"consent_filter_applied":true}',thr:'required true',why:'Required protection missing: suppression.'},
      {id:'PF-04',name:'Seed/proof status',sev:'warning',result:'risk',obs:'{"proof_status":"not_sent","seed_list_present":false}',thr:'approved or waived',why:'Proof is not approved; review before release or record an approved waiver.'},
      {id:'PF-05',name:'Personalization fields available',sev:'required',result:'fail',obs:'{"required":["first_name"],"missing_mappings":["first_name"]}',thr:'no missing mappings',why:'Required personalization mappings missing: first_name.'},
      {id:'PF-06',name:'Link/mirror sanity',sev:'required',result:'fail',obs:'{"unsubscribe_present":true,"mirror_present":false}',thr:'required present',why:'Required link indicators missing: mirror page.'},
      {id:'PF-07',name:'Schedule/timezone sanity',sev:'required',result:'pass',obs:'{"send_at":"2026-11-10T07:00:00Z","timezone":"Europe/Berlin"}',thr:'present',why:'Schedule and timezone are present (format sanity check passed).'},
      {id:'PF-08',name:'Workflow/dependency readiness',sev:'required',result:'fail',obs:'{"status":"pending","dependencies_ok":false,"pending_approvals":1}',thr:'deps ok, 0 pending',why:'Workflow not ready: dependencies not ready, 1 pending approval(s), status=pending.'}
    ]
  }
];

let current = null;
let events = [];
const $ = (id) => document.getElementById(id);
const now = () => new Date().toISOString();

function addEvent(type, payload) {
  events.push({ timestamp: now(), event_type: type, ...payload });
  $('auditLog').textContent = JSON.stringify(events, null, 2);
}

function renderScenario(s) {
  current = s; events = [];
  $('verdictBadge').textContent = s.verdict;
  $('verdictBadge').className = 'badge ' + s.verdict;
  $('summary').textContent = s.summary;
  $('campaignMeta').innerHTML = '<strong>Campaign:</strong> ' + s.id + '<br><strong>Context:</strong> ' + s.meta;
  $('checksBody').innerHTML = s.checks.map(c => `<tr><td><strong>${c.id}</strong><br><span class="muted">${c.name}</span></td><td>${c.sev}</td><td><span class="pill ${c.result}">${c.result}</span></td><td><code>${c.obs}</code><br><span class="muted">${c.thr}</span></td><td>${c.why}</td></tr>`).join('');
  addEvent('run.started', { run_id: 'demo_run', campaign_id: s.id, adapter: { mode:'mock', read_only:true } });
  s.checks.forEach(c => addEvent('check.result', { run_id:'demo_run', check_id:c.id, result:c.result, severity:c.sev }));
  addEvent('run.completed', { run_id:'demo_run', overall_verdict:s.verdict });
  $('approvalMsg').textContent = ''; $('approvalMsg').className = 'msg';
}

$('scenarioSelect').innerHTML = scenarios.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
$('runBtn').addEventListener('click', () => renderScenario(scenarios.find(s => s.id === $('scenarioSelect').value)));
$('rejectBtn').addEventListener('click', () => {
  if (!current) return;
  const approver = $('approver').value.trim() || 'Named Approver';
  addEvent('approval.decision', { run_id:'demo_run', decision:'reject', original_verdict:current.verdict, approver:{name:approver} });
  $('approvalMsg').textContent = 'Rejection recorded in audit trail.'; $('approvalMsg').className = 'msg ok';
});
$('approvalForm').addEventListener('submit', (e) => {
  e.preventDefault();
  if (!current) return;
  const approver = $('approver').value.trim();
  const reason = $('reason').value.trim();
  if (!approver) { $('approvalMsg').textContent = 'Named approver is required.'; $('approvalMsg').className='msg error'; return; }
  if ((current.verdict === 'FAIL' || current.verdict === 'NOT_READY') && reason.length < 15) {
    $('approvalMsg').textContent = 'FAIL/NOT_READY override requires a written reason of at least 15 characters.'; $('approvalMsg').className='msg error'; return;
  }
  const decision = (current.verdict === 'FAIL' || current.verdict === 'NOT_READY') ? 'approve_override' : 'approve';
  addEvent('approval.decision', { run_id:'demo_run', decision, original_verdict:current.verdict, approver:{name:approver}, reason: reason || null });
  if (decision === 'approve_override') {
    const failed = current.checks.filter(c => c.sev === 'required' && (c.result === 'fail' || c.result === 'not_ready')).map(c => c.id);
    addEvent('approval.override', { run_id:'demo_run', original_verdict:current.verdict, failed_required_checks:failed, approver:{name:approver}, reason });
  }
  $('approvalMsg').textContent = decision === 'approve_override' ? 'Override recorded. approval.override was logged separately.' : 'Approval recorded in audit trail.';
  $('approvalMsg').className = 'msg ok';
});
renderScenario(scenarios[0]);
