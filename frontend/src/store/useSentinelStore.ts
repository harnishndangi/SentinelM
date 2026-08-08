import { create } from 'zustand';
import { MLModelItem, FeatureDriftItem, RecoveryActivity, IncidentItem } from '@/types';

interface SentinelState {
  // Production stats
  activeModelName: string;
  activeModelVersion: string;
  activeModelAlgorithm: string;
  modelHealth: number; // percentage, e.g., 82
  healthTrend: number; // e.g., -8.7
  prAuc: number; // 0.94
  prAucTrend: number; // +1.8
  recall: number; // 93.2
  openIncidentsCount: number;

  // Drift stats
  dataDriftLevel: 'High' | 'Medium' | 'Low';
  dataDriftPercentage: number; // e.g. 85
  predictionDriftLevel: 'High' | 'Medium' | 'Low';
  predictionDriftPercentage: number; // e.g. 45
  
  // Lists
  models: MLModelItem[];
  driftingFeatures: FeatureDriftItem[];
  recoveryActivities: RecoveryActivity[];
  incidents: IncidentItem[];

  // Actions
  injectDrift: (featureName?: string) => void;
  registerModel: (model: Omit<MLModelItem, 'id' | 'updatedAt'>) => void;
  promoteModel: (id: string) => void;
  rollbackModel: (id: string) => void;
  archiveModel: (id: string) => void;
}

export const useSentinelStore = create<SentinelState>((set, get) => ({
  activeModelName: 'FraudDetector',
  activeModelVersion: 'v17',
  activeModelAlgorithm: 'XGBoost',
  modelHealth: 82,
  healthTrend: -8.7,
  prAuc: 0.94,
  prAucTrend: 1.8,
  recall: 93.2,
  openIncidentsCount: 3,

  dataDriftLevel: 'High',
  dataDriftPercentage: 85,
  predictionDriftLevel: 'Medium',
  predictionDriftPercentage: 45,

  models: [
    {
      id: 'm-17',
      name: 'FraudDetector',
      version: 'v17',
      algorithm: 'XGBoost',
      status: 'PRODUCTION',
      prAuc: 0.94,
      recall: 93.2,
      f1Score: 0.91,
      updatedAt: '2 hours ago',
      isActive: true,
    },
    {
      id: 'm-18',
      name: 'FraudDetector',
      version: 'v18',
      algorithm: 'LightGBM',
      status: 'CANDIDATE',
      prAuc: 0.96,
      recall: 95.1,
      f1Score: 0.93,
      updatedAt: '12m ago',
      isActive: false,
    },
    {
      id: 'm-16',
      name: 'FraudDetector',
      version: 'v16',
      algorithm: 'XGBoost',
      status: 'ARCHIVED',
      prAuc: 0.91,
      recall: 89.4,
      f1Score: 0.88,
      updatedAt: '3 days ago',
      isActive: false,
    },
  ],

  driftingFeatures: [
    {
      featureName: 'transaction_amount',
      driftScore: 0.28,
      pValue: 0.001,
      status: 'High',
      testType: 'Kolmogorov-Smirnov',
      trend: 'up',
    },
    {
      featureName: 'device_type',
      driftScore: 0.19,
      pValue: 0.024,
      status: 'Medium',
      testType: 'Population Stability Index',
      trend: 'up',
    },
    {
      featureName: 'ip_risk_score',
      driftScore: 0.12,
      pValue: 0.082,
      status: 'Low',
      testType: 'Wasserstein Distance',
      trend: 'stable',
    },
  ],

  recoveryActivities: [
    {
      id: 'act-1',
      title: '→ Canary evaluation running',
      timeAgo: 'Just now',
      status: 'running',
      isCurrent: true,
    },
    {
      id: 'act-2',
      title: '✓ Candidate v18 trained',
      timeAgo: '12m ago',
      status: 'completed',
    },
    {
      id: 'act-3',
      title: '✓ Dataset snapshot created',
      timeAgo: '45m ago',
      status: 'completed',
    },
  ],

  incidents: [
    {
      id: 'inc-101',
      title: 'Feature Drift Anomaly: transaction_amount threshold exceeded',
      severity: 'Critical',
      affectedModel: 'FraudDetector v17',
      createdAt: '15m ago',
      status: 'OPEN',
    },
    {
      id: 'inc-102',
      title: 'Model Recall dropped below target SLA (95%)',
      severity: 'Warning',
      affectedModel: 'FraudDetector v17',
      createdAt: '1h ago',
      status: 'INVESTIGATING',
    },
    {
      id: 'inc-103',
      title: 'High Latency spike in prediction pipeline',
      severity: 'Warning',
      affectedModel: 'FraudDetector v17',
      createdAt: '3h ago',
      status: 'RESOLVED',
    },
  ],

  injectDrift: (featureName = 'transaction_amount') => {
    set((state) => {
      const newHealth = Math.max(40, state.modelHealth - 12);
      const newIncidents = state.openIncidentsCount + 1;
      const newDriftPct = Math.min(98, state.dataDriftPercentage + 8);
      
      const newActivities: RecoveryActivity[] = [
        {
          id: `act-${Date.now()}`,
          title: `→ Autonomous Retraining triggered for ${featureName}`,
          timeAgo: 'Just now',
          status: 'running',
          isCurrent: true,
        },
        ...state.recoveryActivities.map(a => ({ ...a, isCurrent: false })),
      ];

      return {
        modelHealth: newHealth,
        healthTrend: state.healthTrend - 5.2,
        openIncidentsCount: newIncidents,
        dataDriftPercentage: newDriftPct,
        dataDriftLevel: 'High',
        recoveryActivities: newActivities,
      };
    });
  },

  registerModel: (newModel) => {
    const id = `m-${Date.now()}`;
    const modelItem: MLModelItem = {
      ...newModel,
      id,
      updatedAt: 'Just now',
    };
    set((state) => ({
      models: [modelItem, ...state.models],
    }));
  },

  promoteModel: (id) => {
    set((state) => {
      const target = state.models.find((m) => m.id === id);
      if (!target) return state;

      const updatedModels = state.models.map((m) => {
        if (m.id === id) {
          return { ...m, status: 'PRODUCTION' as const, isActive: true };
        }
        if (m.status === 'PRODUCTION') {
          return { ...m, status: 'CANDIDATE' as const, isActive: false };
        }
        return m;
      });

      return {
        models: updatedModels,
        activeModelVersion: target.version,
        activeModelAlgorithm: target.algorithm,
        modelHealth: 96,
        healthTrend: 14.2,
        prAuc: target.prAuc,
        recoveryActivities: [
          {
            id: `act-${Date.now()}`,
            title: `✓ Model ${target.version} promoted to PRODUCTION`,
            timeAgo: 'Just now',
            status: 'completed',
          },
          ...state.recoveryActivities,
        ],
      };
    });
  },

  rollbackModel: (id) => {
    set((state) => {
      const target = state.models.find((m) => m.id === id);
      if (!target) return state;

      const updatedModels = state.models.map((m) => {
        if (m.id === id) {
          return { ...m, status: 'PRODUCTION' as const, isActive: true };
        }
        if (m.status === 'PRODUCTION') {
          return { ...m, status: 'ARCHIVED' as const, isActive: false };
        }
        return m;
      });

      return {
        models: updatedModels,
        activeModelVersion: target.version,
        activeModelAlgorithm: target.algorithm,
        modelHealth: 88,
        recoveryActivities: [
          {
            id: `act-${Date.now()}`,
            title: `↺ Rollback executed to ${target.version}`,
            timeAgo: 'Just now',
            status: 'completed',
          },
          ...state.recoveryActivities,
        ],
      };
    });
  },

  archiveModel: (id) => {
    set((state) => ({
      models: state.models.map((m) =>
        m.id === id ? { ...m, status: 'ARCHIVED' as const, isActive: false } : m
      ),
    }));
  },
}));
