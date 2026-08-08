'use client';

export default function SettingsPage() {
  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Platform Settings</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Manage SentinelML backend connections, database ORM parameters, and drift detection engines.
          </p>
        </div>
      </div>

      <div className="bg-surface card-border rounded-lg p-lg space-y-6 max-w-3xl">
        <div>
          <label className="block text-mono-label text-on-surface mb-1">FastAPI Backend Endpoint</label>
          <input
            type="text"
            defaultValue="http://localhost:8000/api/v1"
            className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table"
          />
        </div>

        <div>
          <label className="block text-mono-label text-on-surface mb-1">Statistical Test Algorithm</label>
          <select className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table">
            <option>Two-Sample Kolmogorov-Smirnov Test</option>
            <option>Population Stability Index (PSI)</option>
            <option>Wasserstein Distance (Earth Mover's)</option>
            <option>Chi-Square Goodness of Fit</option>
          </select>
        </div>

        <div>
          <label className="block text-mono-label text-on-surface mb-1">Self-Healing Automation Policy</label>
          <select className="w-full bg-surface-dim border border-outline-variant rounded p-2 text-on-surface font-mono-table">
            <option>Auto-Promote Candidate Model on Passing Canary Evaluation</option>
            <option>Require Manual Approval for Production Promotion</option>
            <option>Fallback to Baseline Model on Critical Incidents</option>
          </select>
        </div>

        <button
          onClick={() => alert('Settings saved successfully.')}
          className="bg-primary text-on-primary font-mono-label font-bold px-4 py-2 rounded hover:bg-primary-fixed transition-colors"
        >
          Save Configuration
        </button>
      </div>
    </main>
  );
}
