<template>
  <section class="section-list">
    <div class="section-header">
      <h2>已加载文档</h2>
      <button class="btn btn-primary" @click="openUploadForm">+ 上传文档</button>
      <input
        ref="fileInput"
        type="file"
        accept=".docx,.pdf"
        style="display: none"
        @change="handleFileChange"
      />
    </div>

    <div v-if="uploading" class="loading">上传处理中...</div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <table v-else-if="files.length > 0" class="entry-table">
      <thead>
        <tr>
          <th class="col-name">文件名</th>
          <th class="col-collection">所属集合</th>
          <th class="col-sid">来源ID</th>
          <th class="col-action">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="file in files" :key="file.source_id">
          <td class="col-name">{{ file.file_name }}</td>
          <td class="col-collection">{{ file.collection_name }}</td>
          <td class="col-sid">{{ file.source_id }}</td>
          <td class="col-action">
            <button class="btn btn-danger" @click="confirmDelete(file)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="empty">暂无已加载文档</div>

    <div v-if="showUploadForm" class="modal-overlay" @click.self="!uploading && (showUploadForm = false)">
      <div class="modal">
        <div class="modal-header">
          <h3>上传文档到集合</h3>
          <button v-if="!uploading" class="btn-close" @click="showUploadForm = false">&times;</button>
        </div>
        <div v-if="uploading" class="loading">上传处理中...</div>
        <div v-else-if="uploadSuccess" class="success-msg">✅ 上传成功</div>
        <div v-else-if="uploadError" class="error">❌ {{ uploadError }}</div>
        <form v-if="!uploading && !uploadSuccess && !uploadError" @submit.prevent="triggerFileSelect">
          <div class="form-field">
            <label for="upload-collection">目标集合 <span class="required">*</span></label>
            <select id="upload-collection" v-model="uploadCollection" required>
              <option value="" disabled>请选择集合</option>
              <option v-for="col in collections" :key="col.name" :value="col.name">
                {{ col.name }}{{ col.description ? ' - ' + col.description : '' }}
              </option>
            </select>
          </div>
          <div v-if="selectedFile" class="form-field">
            <label>已选文件</label>
            <div class="selected-file">{{ selectedFile.name }}</div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn" @click="showUploadForm = false">取消</button>
            <button type="button" class="btn btn-primary" @click="triggerFileSelect" :disabled="!uploadCollection">
              选择文件
            </button>
          </div>
        </form>
        <div v-if="uploadSuccess || uploadError" class="modal-actions">
          <button class="btn btn-primary" @click="closeUpload">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="btn-close" @click="deleteTarget = null">&times;</button>
        </div>
        <div class="modal-body">
          <p>确定要删除 <strong>{{ deleteTarget.file_name }}</strong> 吗？</p>
          <p class="hint">
            将从集合「{{ deleteTarget.collection_name }}」中删除 source_id={{ deleteTarget.source_id }} 的所有向量化分块。
          </p>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="deleteTarget = null">取消</button>
          <button class="btn btn-danger" :disabled="deleting" @click="handleDelete">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import { ref, onMounted } from 'vue'
import { fetchDocuments, uploadDocument, deleteDocument, fetchCollections } from '../api/entries.js'

export default {
  name: 'DocumentsPage',
  setup() {
    const files = ref([])
    const loading = ref(false)
    const uploading = ref(false)
    const error = ref('')
    const fileInput = ref(null)
    const deleteTarget = ref(null)
    const deleting = ref(false)

    const collections = ref([])
    const showUploadForm = ref(false)
    const uploadCollection = ref('')
    const selectedFile = ref(null)
    const uploadSuccess = ref(false)
    const uploadError = ref('')

    async function load() {
      loading.value = true
      error.value = ''
      try {
        const res = await fetchDocuments()
        files.value = res.items || []
      } catch (e) {
        error.value = '加载失败: ' + e.message
      } finally {
        loading.value = false
      }
    }

    async function loadCollections() {
      try {
        const res = await fetchCollections()
        collections.value = res.items || []
      } catch {}
    }

    function openUploadForm() {
      uploadCollection.value = ''
      selectedFile.value = null
      showUploadForm.value = true
    }

    function triggerFileSelect() {
      if (!uploadCollection.value) return
      fileInput.value.click()
    }

    async function handleFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      selectedFile.value = file
      uploading.value = true
      uploadSuccess.value = false
      uploadError.value = ''
      try {
        await uploadDocument(file, uploadCollection.value)
        e.target.value = ''
        selectedFile.value = null
        uploadSuccess.value = true
        await load()
      } catch (e) {
        uploadError.value = e.message
      } finally {
        uploading.value = false
      }
    }

    function closeUpload() {
      showUploadForm.value = false
      uploadSuccess.value = false
      uploadError.value = ''
    }

    function confirmDelete(file) {
      deleteTarget.value = file
    }

    async function handleDelete() {
      if (!deleteTarget.value) return
      deleting.value = true
      try {
        await deleteDocument(deleteTarget.value.source_id)
        deleteTarget.value = null
        await load()
      } catch (e) {
        error.value = '删除失败: ' + e.message
        deleteTarget.value = null
      } finally {
        deleting.value = false
      }
    }

    onMounted(async () => {
      await loadCollections()
      await load()
    })

    return {
      files, loading, uploading, error, fileInput,
      collections, showUploadForm, uploadCollection, selectedFile,
      openUploadForm, triggerFileSelect, handleFileChange, closeUpload,
      uploadSuccess, uploadError,
      deleteTarget, deleting, confirmDelete, handleDelete,
    }
  },
}
</script>

<style scoped>
.selected-file {
  padding: 8px 12px;
  background: #f0f4ff;
  border-radius: 6px;
  font-size: 14px;
  color: #2563eb;
}

.form-field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  background: #fff;
  cursor: pointer;
}

.form-field select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
</style>
