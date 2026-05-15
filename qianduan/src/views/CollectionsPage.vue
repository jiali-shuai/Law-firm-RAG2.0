<template>
  <section class="section-list">
    <div class="section-header">
      <h2>向量集合列表</h2>
      <button class="btn btn-primary" @click="showForm = true">+ 新增集合</button>
    </div>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <table v-else-if="collections.length > 0" class="entry-table">
      <thead>
        <tr>
          <th class="col-name">集合名称</th>
          <th class="col-desc">描述</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(col, idx) in collections" :key="idx">
          <td class="col-name">{{ col.name || '-' }}</td>
          <td class="col-desc">{{ col.description || '-' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">暂无集合</div>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <div class="modal-header">
          <h3>新增向量集合</h3>
          <button class="btn-close" @click="showForm = false">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="form-field">
            <label for="name">集合名称 <span class="required">*</span></label>
            <input id="name" v-model="form.name" type="text" placeholder="输入集合名称" required />
          </div>
          <div class="form-field">
            <label for="desc">描述 <span class="required">*</span></label>
            <textarea id="desc" v-model="form.description" placeholder="输入集合描述" required rows="4"></textarea>
          </div>
          <div v-if="submitError" class="form-error">{{ submitError }}</div>
          <div class="modal-actions">
            <button type="button" class="btn" @click="showForm = false">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="submitting">{{ submitting ? '提交中...' : '确认新增' }}</button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<script>
import { ref, onMounted } from 'vue'
import { fetchCollections, createCollection } from '../api/entries.js'

export default {
  name: 'CollectionsPage',
  setup() {
    const collections = ref([])
    const loading = ref(false)
    const error = ref('')
    const showForm = ref(false)
    const form = ref({ name: '', description: '' })
    const submitting = ref(false)
    const submitError = ref('')

    async function load() {
      loading.value = true
      error.value = ''
      try {
        const res = await fetchCollections()
        collections.value = res.items || []
      } catch (e) {
        error.value = '加载失败: ' + e.message
      } finally {
        loading.value = false
      }
    }

    async function handleSubmit() {
      submitError.value = ''
      submitting.value = true
      try {
        await createCollection(form.value.name, form.value.description)
        showForm.value = false
        form.value = { name: '', description: '' }
        await load()
      } catch (e) {
        submitError.value = e.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(load)

    return { collections, loading, error, showForm, form, submitting, submitError, handleSubmit }
  },
}
</script>
