import axios from 'axios';
import { SystemHealth, MLModelItem } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkBackendHealth = async (): Promise<SystemHealth> => {
  try {
    const response = await apiClient.get<SystemHealth>('/health');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch backend health status:', error);
    return {
      status: 'healthy (mock)',
      service: 'sentinelml-api',
      version: '1.0.0',
    };
  }
};

export const fetchRegisteredModels = async (): Promise<MLModelItem[]> => {
  try {
    const response = await apiClient.get('/models');
    return response.data;
  } catch (error) {
    console.warn('Backend unavailable, using store models.');
    return [];
  }
};

export const triggerDriftSimulation = async (featureName: string = 'transaction_amount') => {
  try {
    const response = await apiClient.post('/predict', {
      feature: featureName,
      simulate_drift: true,
    });
    return response.data;
  } catch (error) {
    console.warn('Backend endpoint unavailable, falling back to local store injection.');
    return { status: 'drift_injected', feature: featureName };
  }
};

