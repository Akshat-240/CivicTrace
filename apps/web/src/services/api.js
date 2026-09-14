const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Helper to perform fetch requests and handle JSON / errors centrally.
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}/api/v1${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch (e) {
        // Ignore json parse error if not JSON
      }
      throw new Error(`API Error ${response.status}: ${errorMessage}`);
    }
    
    // Some endpoints might return 204 No Content or empty responses
    if (response.status === 204) {
      return null;
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
}

// ------------------------------------------------------------------
// Incidents
// ------------------------------------------------------------------

export async function getIncidents(skip = 0, limit = 20) {
  return fetchAPI(`/incidents?skip=${skip}&limit=${limit}`);
}

export async function getIncident(id) {
  return fetchAPI(`/incidents/${id}`);
}

export async function createIncident(data) {
  return fetchAPI('/incidents', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ------------------------------------------------------------------
// Associated resources
// ------------------------------------------------------------------

export async function getIncidentEvidence(id) {
  return fetchAPI(`/incidents/${id}/evidence`);
}

export async function getIncidentTimeline(id) {
  return fetchAPI(`/incidents/${id}/timeline`);
}

export async function getIncidentAccountability(id) {
  return fetchAPI(`/incidents/${id}/accountability`);
}

export async function getIncidentVerification(id) {
  return fetchAPI(`/incidents/${id}/verification`);
}

// ------------------------------------------------------------------
// Actions
// ------------------------------------------------------------------

export async function assignJurisdiction(id) {
  return fetchAPI(`/incidents/${id}/assign-jurisdiction`, { method: 'POST' });
}

export async function prioritizeIncident(id) {
  return fetchAPI(`/incidents/${id}/prioritize`, { method: 'POST' });
}

export async function startIncidentSLA(id) {
  return fetchAPI(`/incidents/${id}/start-sla`, { method: 'POST' });
}

export async function evaluateIncidentSLA(id) {
  return fetchAPI(`/incidents/${id}/evaluate-sla`, { method: 'POST' });
}

export async function verifyResolution(id) {
  return fetchAPI(`/incidents/${id}/verify-resolution`, { method: 'POST' });
}

export async function submitResolutionEvidence(id, data) {
  return fetchAPI(`/incidents/${id}/submit-resolution`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function humanVerifyResolution(id, data) {
  return fetchAPI(`/incidents/${id}/human-verify`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function closeIncident(id) {
  return fetchAPI(`/incidents/${id}/close`, { method: 'POST' });
}

export async function addIncidentEvidence(id, data) {
  return fetchAPI(`/incidents/${id}/evidence`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
