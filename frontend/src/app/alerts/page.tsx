'use client';

import { useState } from 'react';

export default function AlertsPage() {
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [slackAlerts, setSlackAlerts] = useState(true);
  const [pagerDutyAlerts, setPagerDutyAlerts] = useState(false);

  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Alert Rules & Channels</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Configure automated drift, degradation, and self-healing threshold alerts.
          </p>
        </div>
      </div>

      <div className="bg-surface card-border rounded-lg p-lg space-y-6 max-w-3xl">
        <h3 className="text-display-md text-on-surface text-[18px] mb-4">Notification Channels</h3>

        <div className="flex items-center justify-between p-3 rounded bg-surface-container-low border border-outline-variant">
          <div>
            <div className="text-on-surface font-semibold">Slack Webhook Alerts</div>
            <div className="text-body-sm text-on-surface-variant">Send real-time drift alerts to #ml-reliability</div>
          </div>
          <input
            type="checkbox"
            checked={slackAlerts}
            onChange={(e) => setSlackAlerts(e.target.checked)}
            className="w-5 h-5 accent-primary"
          />
        </div>

        <div className="flex items-center justify-between p-3 rounded bg-surface-container-low border border-outline-variant">
          <div>
            <div className="text-on-surface font-semibold">Email Notifications</div>
            <div className="text-body-sm text-on-surface-variant">Send summary emails to mlops-team@sentinelml.io</div>
          </div>
          <input
            type="checkbox"
            checked={emailAlerts}
            onChange={(e) => setEmailAlerts(e.target.checked)}
            className="w-5 h-5 accent-primary"
          />
        </div>

        <div className="flex items-center justify-between p-3 rounded bg-surface-container-low border border-outline-variant">
          <div>
            <div className="text-on-surface font-semibold">PagerDuty On-Call Trigger</div>
            <div className="text-body-sm text-on-surface-variant">Trigger PagerDuty incident when SLA drops &lt; 80%</div>
          </div>
          <input
            type="checkbox"
            checked={pagerDutyAlerts}
            onChange={(e) => setPagerDutyAlerts(e.target.checked)}
            className="w-5 h-5 accent-primary"
          />
        </div>
      </div>
    </main>
  );
}
