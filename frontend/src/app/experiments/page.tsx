'use client';

export default function ExperimentsPage() {
  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Experiments & MLflow Runs</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Track hyperparameter tuning runs, MLflow metadata, and metric comparisons.
          </p>
        </div>
      </div>
      <div className="bg-surface card-border rounded-lg p-lg text-on-surface-variant font-mono-table text-body-md">
        SentinelML Experiments module active.
      </div>
    </main>
  );
}
