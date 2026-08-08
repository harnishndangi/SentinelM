'use client';

export default function DataPage() {
  return (
    <main className="p-6 md:p-8 flex-1 overflow-y-auto bg-background w-full h-full">
      <div className="flex justify-between items-center mb-xl">
        <div>
          <h1 className="text-display-lg font-display-lg text-on-surface mb-xs">Dataset Snapshots</h1>
          <p className="text-body-md font-body-md text-on-surface-variant">
            Manage training reference data, inference data partitions, and schema versions.
          </p>
        </div>
      </div>
      <div className="bg-surface card-border rounded-lg p-lg text-on-surface-variant font-mono-table text-body-md">
        Dataset Snapshots & Reference Payloads.
      </div>
    </main>
  );
}
