import axios from 'axios';

// Create axios instance with base URL
const API = axios.create({
  baseURL: '/api'
});

// Add authorization header interceptor
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await API.post('/auth/login', { username, password });
    return response.data;
  },
  
  logout: async () => {
    const response = await API.post('/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await API.get('/auth/me');
    return response.data;
  }
};

// Patients API
export const patientsAPI = {
  getAllPatients: async () => {
    const response = await API.get('/patients');
    return response.data;
  },
  
  getPatientById: async (id: string) => {
    const response = await API.get(`/patients/${id}`);
    return response.data;
  },
  
  getRecentPatients: async () => {
    const response = await API.get('/patients/recent');
    return response.data;
  },
  
  getPatientAppointments: async (patientId: string) => {
    const response = await API.get(`/patients/${patientId}/appointments`);
    return response.data;
  }
};

// Appointments API
export const appointmentsAPI = {
  getAppointmentsByProvider: async (providerId: string) => {
    const response = await API.get(`/appointments?provider_id=${providerId}`);
    return response.data;
  },
  
  getAppointmentById: async (id: string) => {
    const response = await API.get(`/appointments/${id}`);
    return response.data;
  },
  
  getRecentAppointments: async (providerId: string) => {
    const response = await API.get(`/appointments/recent?provider_id=${providerId}`);
    return response.data;
  },
  
  updateAppointmentStatus: async (id: string, status: string) => {
    const response = await API.put(`/appointments/${id}/status`, { status });
    return response.data;
  }
};

// Messages API
export const messagesAPI = {
  getConversations: async (providerId: string) => {
    const response = await API.get(`/messages/conversations?provider_id=${providerId}`);
    return response.data;
  },
  
  getConversation: async (providerId: string, patientId: string) => {
    const response = await API.get(`/messages/${patientId}?provider_id=${providerId}`);
    return response.data;
  },
  
  sendMessage: async (providerId: string, patientId: string, content: string) => {
    const response = await API.post('/messages', {
      provider_id: providerId,
      patient_id: patientId,
      content
    });
    return response.data;
  },
  
  getUnreadCount: async (providerId: string) => {
    const response = await API.get(`/messages/unread/count?provider_id=${providerId}`);
    return response.data;
  },
  
  getRecentMessages: async (providerId: string) => {
    const response = await API.get(`/messages/recent?provider_id=${providerId}`);
    return response.data;
  }
};

// Health Information API
export const healthInfoAPI = {
  getAllHealthInfo: async () => {
    const response = await API.get('/health-info');
    return response.data;
  },
  
  getHealthInfoByLanguage: async (language: string) => {
    const response = await API.get(`/health-info/${language}`);
    return response.data;
  },
  
  createHealthInfo: async (title: string, content: string, language: string) => {
    const response = await API.post('/health-info', {
      title,
      content,
      language
    });
    return response.data;
  }
};

// Dashboard API
export const dashboardAPI = {
  getStats: async (providerId: string) => {
    const response = await API.get(`/dashboard/stats?provider_id=${providerId}`);
    return response.data;
  },
  
  getRecentPatients: async () => {
    const response = await API.get('/dashboard/recent-patients');
    return response.data;
  },
  
  getRecentAppointments: async (providerId: string) => {
    const response = await API.get(`/dashboard/recent-appointments?provider_id=${providerId}`);
    return response.data;
  },
  
  getRecentMessages: async (providerId: string) => {
    const response = await API.get(`/dashboard/recent-messages?provider_id=${providerId}`);
    return response.data;
  }
};