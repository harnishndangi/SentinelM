export interface SystemHealth {
  status: string;
  service: string;
  version: string;
}

export interface MetricSummary {
  modelCount: number;
  activeDriftAlerts: number;
  selfHealingActions: number;
  systemHealthStatus: 'healthy' | 'degraded' | 'critical';
}

export type ModelStatus = 'PRODUCTION' | 'CANDIDATE' | 'ARCHIVED';

export interface MLModelItem {
  id: string;
  name: string;
  version: string;
  algorithm: string;
  status: ModelStatus;
  prAuc: number;
  recall?: number;
  f1Score?: number;
  updatedAt: string;
  isActive?: boolean;
}

export interface FeatureDriftItem {
  featureName: string;
  driftScore: number; // e.g. 0.0 to 1.0 (KS statistic)
  pValue: number;
  status: 'High' | 'Medium' | 'Low' | 'Normal';
  testType: string; // e.g. 'Kolmogorov-Smirnov', 'PSI'
  trend: 'up' | 'down' | 'stable';
}

export interface RecoveryActivity {
  id: string;
  title: string;
  timeAgo: string;
  status: 'running' | 'completed' | 'failed';
  isCurrent?: boolean;
}

export interface IncidentItem {
  id: string;
  title: string;
  severity: 'Critical' | 'Warning' | 'Info';
  affectedModel: string;
  createdAt: string;
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED';
}

