<template>
  <div id="app-container">
    <header class="app-header">
      <h1>RAG 向量库管理</h1>
      <div class="header-status">
        <span :class="['status-dot', apiOnline ? 'online' : 'offline']"></span>
        {{ apiOnline ? '服务在线' : '服务离线' }}
      </div>
    </header>

    <nav class="nav-bar">
      <router-link class="nav-link" to="/collections">向量集合</router-link>
      <router-link class="nav-link" to="/documents">文档管理</router-link>
      <router-link class="nav-link" to="/chat">智能问答</router-link>
      <router-link class="nav-link" to="/params">检索参数</router-link>
    </nav>

    <main class="app-main">
      <div v-if="!apiOnline && !loading" class="error">
        无法连接到后端服务，请确认 api.py 已启动 (端口 8000)
      </div>
      <router-view v-else />
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { checkHealth } from './api/entries.js'

export default {
  name: 'App',
  setup() {
    const apiOnline = ref(false)
    const loading = ref(true)

    onMounted(async () => {
      try {
        await checkHealth()
        apiOnline.value = true
      } catch {
        apiOnline.value = false
      } finally {
        loading.value = false
      }
    })

    return { apiOnline, loading }
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f7fa;
  color: #333;
  min-height: 100vh;
}

#app-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.app-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online { background: #22c55e; }
.status-dot.offline { background: #ef4444; }

.nav-bar {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
}

.nav-link {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  text-decoration: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.15s;
}

.nav-link:hover { color: #2563eb; }

.nav-link.router-link-active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.btn {
  padding: 8px 18px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #fff;
  color: #333;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn:hover { border-color: #999; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.btn-primary:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-danger {
  color: #ef4444;
  border-color: #fecaca;
  background: #fff;
}

.btn-danger:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}

.loading, .empty, .error {
  text-align: center;
  padding: 48px 0;
  color: #999;
  font-size: 14px;
}

.error { color: #ef4444; }

.entry-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.entry-table th, .entry-table td {
  padding: 12px 16px;
  text-align: left;
  font-size: 14px;
  border-bottom: 1px solid #eee;
}

.entry-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #555;
}

.entry-table tbody tr:hover { background: #f8faff; }

.col-name { width: 220px; font-weight: 500; }
.col-desc { color: #555; }
.col-collection { width: 180px; color: #2563eb; font-weight: 500; }
.col-sid { width: 80px; color: #666; text-align: center; }
.col-count { width: 100px; color: #666; text-align: center; }
.col-action { width: 100px; text-align: center; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: #fff;
  border-radius: 12px;
  width: 520px;
  max-width: 95vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.modal-sm { width: 400px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.modal-header h3 { font-size: 17px; }

.btn-close {
  background: none;
  border: none;
  font-size: 22px;
  color: #999;
  cursor: pointer;
}

.btn-close:hover { color: #333; }

.modal form { padding: 20px 24px 24px; }

.modal-body { padding: 16px 24px; }

.modal-body p { font-size: 14px; margin-bottom: 8px; }

.modal-body .hint { color: #999; font-size: 13px; }

.form-field { margin-bottom: 16px; }

.form-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #555;
  margin-bottom: 6px;
}

.required { color: #ef4444; }

.form-field input, .form-field textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s;
}

.form-field input:focus, .form-field textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-error {
  color: #ef4444;
  font-size: 13px;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
  padding: 0 24px 24px;
}
</style>
