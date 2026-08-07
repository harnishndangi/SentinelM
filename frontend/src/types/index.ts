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
