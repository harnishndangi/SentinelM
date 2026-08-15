'use client';

import React, { useState } from 'react';
import {
  Bell,
  Slack,
  Mail,
  Smartphone,
  Webhook,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Send,
  X,
  Sliders,
  ShieldAlert,
  Clock,
  ExternalLink,
  Check,
  RefreshCw,
} from 'lucide-react';
import { StatusBadge, SeverityBadge, MetricCard, DataTable, AlertBanner } from '@/components/ui';

export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  channels: string[];
  enabled: boolean;
}

export interface TriggeredAlertItem {
  id: string;
  ruleName: string;
  triggeredAt: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  channelSent: string;
  status: 'DELIVERED' | 'FAILED' | 'PENDING';
  latency: string;
}

const INITIAL_RULES: AlertRule[] = [
  {
    id: 'rule-01',
    name: 'Feature Drift Anomaly (PSI Threshold)',
    metric: 'Population Stability Index (PSI)',
    condition: '>',
    threshold: '0.20 PSI',
    severity: 'CRITICAL',
    channels: ['Slack #ml-reliability', 'PagerDuty On-Call'],
    enabled: true,
  },
  {
    id: 'rule-02',
    name: 'Model SLA Recall Degradation',
    metric: 'Model Recall SLA Score',
    condition: '<',
    threshold: '90.0%',
    severity: 'HIGH',
    channels: ['Slack #ml-reliability', 'Email MLOps Team'],
    enabled: true,
  },
  {
    id: 'rule-03',
    name: 'Inference P95 Latency Spike',
    metric: 'P95 Latency (ms)',
    condition: '>',
    threshold: '50.0 ms',
    severity: 'MEDIUM',
    channels: ['Slack #ml-reliability'],
    enabled: true,
  },
  {
    id: 'rule-04',
    name: 'Prediction Pipeline Error Rate',
    metric: 'HTTP 500 Error Rate',
    condition: '>',
    threshold: '0.10%',
    severity: 'CRITICAL',
    channels: ['Slack #ml-reliability', 'PagerDuty On-Call', 'Custom Webhook'],
    enabled: true,
  },
  {
    id: 'rule-05',
    name: 'Covariate Shift in Mobile OS Feature',
    metric: 'KS-Test p-value',
    condition: '<',
    threshold: '0.01',
    severity: 'LOW',
    channels: ['Email MLOps Team'],
    enabled: false,
  },
];

const INITIAL_HISTORY: TriggeredAlertItem[] = [
  {
    id: 'trig-901',
    ruleName: 'Feature Drift Anomaly (PSI Threshold)',
    triggeredAt: '15m ago',
    severity: 'CRITICAL',
    channelSent: 'Slack #ml-reliability',
    status: 'DELIVERED',
    latency: '1.2s',
  },
  {
    id: 'trig-902',
    ruleName: 'Model SLA Recall Degradation',
    triggeredAt: '1h ago',
    severity: 'HIGH',
    channelSent: 'Email MLOps Team',
    status: 'DELIVERED',
    latency: '3.4s',
  },
  {
    id: 'trig-903',
    ruleName: 'Inference P95 Latency Spike',
    triggeredAt: '3h ago',
    severity: 'MEDIUM',
    channelSent: 'Slack #ml-reliability',
    status: 'DELIVERED',
    latency: '0.9s',
  },
];

export default function AlertsPage() {
  const [activeTab, setActiveTab] = useState<'RULES' | 'CHANNELS' | 'HISTORY'>('RULES');
  const [rules, setRules] = useState<AlertRule[]>(INITIAL_RULES);
  const [history, setHistory] = useState<TriggeredAlertItem[]>(INITIAL_HISTORY);
  const [notification, setNotification] = useState<string | null>(null);

  // Channel States
  const [slackEnabled, setSlackEnabled] = useState(true);
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/T00/B00/XXXXX');
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [emailRecipients, setEmailRecipients] = useState('mlops-team@sentinelml.io, devops@sentinelml.io');
  const [pagerDutyEnabled, setPagerDutyEnabled] = useState(false);
  const [pagerDutyKey, setPagerDutyKey] = useState('pd-routing-key-99281a');
  const [webhookEnabled, setWebhookEnabled] = useState(true);
  const [webhookUrl, setWebhookUrl] = useState('https://api.company.com/webhooks/sentinelml');

  // Rule Creation Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [ruleMetric, setRuleMetric] = useState('Population Stability Index (PSI)');
  const [ruleCondition, setRuleCondition] = useState('>');
  const [ruleThreshold, setRuleThreshold] = useState('0.25 PSI');
  const [ruleSeverity, setRuleSeverity] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');

  const toggleRule = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r))
    );
  };

  const handleTestSlack = () => {
    setNotification('Test notification payload sent to Slack #ml-reliability channel!');
    setTimeout(() => setNotification(null), 5000);
  };

  const handleTestEmail = () => {
    setNotification(`Test digest email sent to ${emailRecipients}!`);
    setTimeout(() => setNotification(null), 5000);
  };

  const handleTestPagerDuty = () => {
    setNotification('Test PagerDuty incident trigger sent successfully!');
    setTimeout(() => setNotification(null), 5000);
  };

  const handleCreateRule = (e: React.FormEvent) => {
    e.preventDefault();
    const newRule: AlertRule = {
      id: `rule-0${rules.length + 1}`,
      name: ruleName,
      metric: ruleMetric,
      condition: ruleCondition,
      threshold: ruleThreshold,
      severity: ruleSeverity,
      channels: ['Slack #ml-reliability'],
      enabled: true,
    };
    setRules([newRule, ...rules]);
    setIsCreateModalOpen(false);
    setNotification(`Alert rule '${ruleName}' created and activated!`);
    setTimeout(() => setNotification(null), 5000);
  };

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-[#101417] text-slate-100 w-full h-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252E3B] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Bell className="w-7 h-7 text-purple-400" />
              Alert Rules & Notification Channels
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-[#101417] text-purple-300 border border-[#252E3B] font-semibold">
              {rules.filter((r) => r.enabled).length} Active Rules
            </span>
          </div>
          <p className="text-xs font-mono text-[#94a3b8] mt-1">
            Configure automated drift detection, model SLA degradation thresholds, Slack, PagerDuty, and Email alerts
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold font-mono text-xs rounded-lg shadow-md flex items-center gap-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          CREATE ALERT RULE
        </button>
      </div>

      {notification && (
        <AlertBanner type="success" title="Alert System Notice" message={notification} onClose={() => setNotification(null)} />
      )}

      {/* Tabs Row */}
      <div className="flex items-center gap-3 border-b border-[#252E3B] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab('RULES')}
          className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
            activeTab === 'RULES' ? 'bg-purple-600 text-white shadow' : 'text-[#94a3b8] hover:text-white'
          }`}
        >
          <Sliders className="w-4 h-4" />
          Alert Rules Matrix ({rules.length})
        </button>

        <button
          onClick={() => setActiveTab('CHANNELS')}
          className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
            activeTab === 'CHANNELS' ? 'bg-purple-600 text-white shadow' : 'text-[#94a3b8] hover:text-white'
          }`}
        >
          <Send className="w-4 h-4" />
          Notification Channels (4)
        </button>

        <button
          onClick={() => setActiveTab('HISTORY')}
          className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
            activeTab === 'HISTORY' ? 'bg-purple-600 text-white shadow' : 'text-[#94a3b8] hover:text-white'
          }`}
        >
          <Clock className="w-4 h-4" />
          Trigger History ({history.length})
        </button>
      </div>

      {/* TAB 1: ALERT RULES MATRIX */}
      {activeTab === 'RULES' && (
        <div className="space-y-4">
          <DataTable
            columns={[
              {
                key: 'enabled',
                header: 'Status',
                render: (rule: AlertRule) => (
                  <button
                    onClick={() => toggleRule(rule.id)}
                    className={`w-10 h-5 rounded-full p-0.5 transition-colors ${
                      rule.enabled ? 'bg-purple-600' : 'bg-slate-800'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform ${
                        rule.enabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                ),
              },
              {
                key: 'name',
                header: 'Rule Name',
                render: (rule: AlertRule) => (
                  <div>
                    <span className="font-mono font-bold text-white block">{rule.name}</span>
                    <span className="text-[11px] font-mono text-[#94a3b8]">{rule.id}</span>
                  </div>
                ),
              },
              {
                key: 'metric',
                header: 'Monitored Telemetry',
                render: (rule: AlertRule) => (
                  <span className="font-mono text-xs text-purple-300 font-semibold">{rule.metric}</span>
                ),
              },
              {
                key: 'threshold',
                header: 'Condition & Threshold',
                render: (rule: AlertRule) => (
                  <span className="font-mono text-xs text-white bg-[#101417] border border-[#252E3B] px-2.5 py-1 rounded">
                    {rule.condition} {rule.threshold}
                  </span>
                ),
              },
              {
                key: 'severity',
                header: 'Severity',
                render: (rule: AlertRule) => <SeverityBadge severity={rule.severity} size="sm" />,
              },
              {
                key: 'channels',
                header: 'Routing Channels',
                render: (rule: AlertRule) => (
                  <div className="flex flex-wrap gap-1">
                    {rule.channels.map((ch) => (
                      <span key={ch} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#101417] border border-[#252E3B] text-slate-300">
                        {ch}
                      </span>
                    ))}
                  </div>
                ),
              },
              {
                key: 'actions',
                header: 'Actions',
                render: (rule: AlertRule) => (
                  <button
                    onClick={() => toggleRule(rule.id)}
                    className="px-2.5 py-1 text-[11px] font-mono font-semibold bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-300 rounded"
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </button>
                ),
              },
            ]}
            data={rules}
            keyExtractor={(rule: AlertRule) => rule.id}
          />
        </div>
      )}

      {/* TAB 2: NOTIFICATION CHANNELS */}
      {activeTab === 'CHANNELS' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Slack Webhook Card */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <div className="flex items-center gap-3">
                <Slack className="w-6 h-6 text-emerald-400" />
                <div>
                  <h3 className="text-sm font-bold font-mono text-white">Slack Webhook Integration</h3>
                  <p className="text-[11px] font-mono text-[#94a3b8]">Real-time channel alerts for #ml-reliability</p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={slackEnabled}
                onChange={(e) => setSlackEnabled(e.target.checked)}
                className="w-4 h-4 accent-purple-600 cursor-pointer"
              />
            </div>

            <div className="space-y-2 font-mono text-xs">
              <label className="block text-[#94a3b8] font-semibold">Incoming Webhook URL</label>
              <input
                type="text"
                value={slackWebhook}
                onChange={(e) => setSlackWebhook(e.target.value)}
                className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={handleTestSlack}
              className="w-full py-2 bg-purple-600 hover:bg-purple-500 text-white font-mono font-bold text-xs rounded-lg flex items-center justify-center gap-2 shadow"
            >
              <Send className="w-3.5 h-3.5" />
              Send Test Slack Alert
            </button>
          </div>

          {/* Email Notifications Card */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <div className="flex items-center gap-3">
                <Mail className="w-6 h-6 text-sky-400" />
                <div>
                  <h3 className="text-sm font-bold font-mono text-white">Email Digest & Alerts</h3>
                  <p className="text-[11px] font-mono text-[#94a3b8]">Summary emails and critical alert escalation</p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={emailEnabled}
                onChange={(e) => setEmailEnabled(e.target.checked)}
                className="w-4 h-4 accent-purple-600 cursor-pointer"
              />
            </div>

            <div className="space-y-2 font-mono text-xs">
              <label className="block text-[#94a3b8] font-semibold">Recipients Email List (comma separated)</label>
              <input
                type="text"
                value={emailRecipients}
                onChange={(e) => setEmailRecipients(e.target.value)}
                className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={handleTestEmail}
              className="w-full py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono font-bold text-xs rounded-lg flex items-center justify-center gap-2"
            >
              <Send className="w-3.5 h-3.5 text-sky-400" />
              Send Test Email Notification
            </button>
          </div>

          {/* PagerDuty On-Call Card */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <div className="flex items-center gap-3">
                <Smartphone className="w-6 h-6 text-rose-400" />
                <div>
                  <h3 className="text-sm font-bold font-mono text-white">PagerDuty On-Call Incident Trigger</h3>
                  <p className="text-[11px] font-mono text-[#94a3b8]">Trigger high-urgency PagerDuty incidents on SLA breach</p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={pagerDutyEnabled}
                onChange={(e) => setPagerDutyEnabled(e.target.checked)}
                className="w-4 h-4 accent-purple-600 cursor-pointer"
              />
            </div>

            <div className="space-y-2 font-mono text-xs">
              <label className="block text-[#94a3b8] font-semibold">Routing Key / Service Integration Key</label>
              <input
                type="text"
                value={pagerDutyKey}
                onChange={(e) => setPagerDutyKey(e.target.value)}
                className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={handleTestPagerDuty}
              className="w-full py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono font-bold text-xs rounded-lg flex items-center justify-center gap-2"
            >
              <Send className="w-3.5 h-3.5 text-rose-400" />
              Trigger Test PagerDuty Incident
            </button>
          </div>

          {/* Custom Webhook Endpoint Card */}
          <div className="bg-[#101417] border border-[#252E3B] rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <div className="flex items-center gap-3">
                <Webhook className="w-6 h-6 text-purple-400" />
                <div>
                  <h3 className="text-sm font-bold font-mono text-white">Custom Webhook Endpoint</h3>
                  <p className="text-[11px] font-mono text-[#94a3b8]">POST JSON payload to enterprise SIEM or alerting system</p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={webhookEnabled}
                onChange={(e) => setWebhookEnabled(e.target.checked)}
                className="w-4 h-4 accent-purple-600 cursor-pointer"
              />
            </div>

            <div className="space-y-2 font-mono text-xs">
              <label className="block text-[#94a3b8] font-semibold">Custom Webhook Target URL</label>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                className="w-full bg-[#101417] border border-[#252E3B] rounded-lg p-2.5 text-slate-200 outline-none focus:border-purple-500"
              />
            </div>

            <button
              onClick={() => {
                setNotification('Test payload POST request dispatched to custom webhook endpoint!');
                setTimeout(() => setNotification(null), 5000);
              }}
              className="w-full py-2 bg-[#101417] border border-[#252E3B] hover:bg-slate-800 text-slate-200 font-mono font-bold text-xs rounded-lg flex items-center justify-center gap-2"
            >
              <Send className="w-3.5 h-3.5 text-purple-400" />
              Test Custom Webhook
            </button>
          </div>
        </div>
      )}

      {/* TAB 3: TRIGGER HISTORY */}
      {activeTab === 'HISTORY' && (
        <div className="space-y-4">
          <DataTable
            columns={[
              {
                key: 'id',
                header: 'Trigger ID',
                render: (h: TriggeredAlertItem) => <span className="font-mono font-bold text-purple-400">{h.id}</span>,
              },
              {
                key: 'ruleName',
                header: 'Triggered Rule',
                render: (h: TriggeredAlertItem) => <span className="font-mono font-semibold text-white">{h.ruleName}</span>,
              },
              {
                key: 'severity',
                header: 'Severity',
                render: (h: TriggeredAlertItem) => <SeverityBadge severity={h.severity} size="sm" />,
              },
              {
                key: 'channelSent',
                header: 'Target Channel',
                render: (h: TriggeredAlertItem) => (
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#101417] border border-[#252E3B] text-slate-300">
                    {h.channelSent}
                  </span>
                ),
              },
              {
                key: 'status',
                header: 'Delivery Status',
                render: (h: TriggeredAlertItem) => <StatusBadge status={h.status} size="sm" />,
              },
              {
                key: 'latency',
                header: 'Delivery Latency',
                render: (h: TriggeredAlertItem) => <span className="font-mono text-xs text-[#94a3b8]">{h.latency}</span>,
              },
              {
                key: 'triggeredAt',
                header: 'Triggered',
                render: (h: TriggeredAlertItem) => <span className="font-mono text-xs text-[#94a3b8]">{h.triggeredAt}</span>,
              },
            ]}
            data={history}
            keyExtractor={(h: TriggeredAlertItem) => h.id}
          />
        </div>
      )}

      {/* Create Alert Rule Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#101417] border border-[#252E3B] rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#252E3B] pb-3">
              <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
                <Bell className="w-5 h-5 text-purple-400" />
                Configure New Alert Rule
              </h3>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Rule Name</label>
                <input
                  type="text"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  placeholder="e.g. High Feature Drift Warning"
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white outline-none focus:border-purple-500"
                  required
                />
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Monitored Telemetry Metric</label>
                <select
                  value={ruleMetric}
                  onChange={(e) => setRuleMetric(e.target.value)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white outline-none focus:border-purple-500"
                >
                  <option value="Population Stability Index (PSI)">Population Stability Index (PSI)</option>
                  <option value="Model Recall SLA Score">Model Recall SLA Score</option>
                  <option value="P95 Latency (ms)">P95 Latency (ms)</option>
                  <option value="HTTP 500 Error Rate">HTTP 500 Error Rate</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[#94a3b8] mb-1 font-semibold">Condition</label>
                  <select
                    value={ruleCondition}
                    onChange={(e) => setRuleCondition(e.target.value)}
                    className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white outline-none focus:border-purple-500"
                  >
                    <option value=">">Greater than (&gt;)</option>
                    <option value="<">Less than (&lt;)</option>
                    <option value="=">Equals (=)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[#94a3b8] mb-1 font-semibold">Threshold</label>
                  <input
                    type="text"
                    value={ruleThreshold}
                    onChange={(e) => setRuleThreshold(e.target.value)}
                    className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white outline-none focus:border-purple-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[#94a3b8] mb-1 font-semibold">Severity Level</label>
                <select
                  value={ruleSeverity}
                  onChange={(e) => setRuleSeverity(e.target.value as any)}
                  className="w-full bg-[#101417] border border-[#252E3B] rounded-lg px-3 py-2 text-white outline-none focus:border-purple-500"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-[#252E3B]">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 bg-[#101417] border border-[#252E3B] text-[#94a3b8] hover:text-white rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg shadow-md"
                >
                  Activate Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
