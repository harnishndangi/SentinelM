import axios from 'axios';
import { SystemHealth } from '@/types';

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
      status: 'offline',
      service: 'sentinelml-api',
      version: 'unknown',
    };
  }
};
