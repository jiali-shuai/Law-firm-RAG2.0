import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 600000,
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  },
)

export function fetchCollections() {
  return http.get('/collections')
}

export function createCollection(name, description) {
  return http.post('/collections', { name, description })
}

export function fetchDocuments() {
  return http.get('/documents')
}

export function uploadDocument(file, collectionName) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('collection_name', collectionName)
  return http.post('/documents/upload', formData)
}

export function deleteDocument(sourceId) {
  return http.delete(`/documents/${encodeURIComponent(sourceId)}`)
}

export function sendLegalChat(question, sessionId, paramOverrides = {}) {
  return http.post('/legal/chat', {
    question,
    session_id: sessionId,
    param_overrides: paramOverrides,
  })
}

export function checkHealth() {
  return http.get('/health')
}
