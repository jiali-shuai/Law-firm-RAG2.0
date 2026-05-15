<template>
  <div class="params-layout">
    <section class="params-main">
      <div class="section-header">
        <h2>检索参数设置</h2>
        <button class="btn" @click="resetDefaults">恢复默认值</button>
      </div>

      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>

      <div class="params-card">
        <div class="param-row">
          <div class="param-info">
            <span class="param-label">dense_top_k（密集向量检索数量）</span>
            <span class="param-desc">控制语义相似度检索返回的候选数量，值越大召回越多但耗时更长</span>
          </div>
          <div class="param-control">
            <input
              type="range"
              min="3" max="30" step="1"
              v-model.number="currentParams.dense_top_k"
            />
            <span class="param-value">{{ currentParams.dense_top_k }}</span>
          </div>
        </div>

        <div class="param-row">
          <div class="param-info">
            <span class="param-label">sparse_top_k（稀疏向量检索数量）</span>
            <span class="param-desc">控制关键词匹配检索返回的候选数量，值越大对关键词越敏感</span>
          </div>
          <div class="param-control">
            <input
              type="range"
              min="3" max="30" step="1"
              v-model.number="currentParams.sparse_top_k"
            />
            <span class="param-value">{{ currentParams.sparse_top_k }}</span>
          </div>
        </div>

        <div class="param-row">
          <div class="param-info">
            <span class="param-label">alpha（混合检索权重）</span>
            <span class="param-desc">密集向量与稀疏向量的融合比例，越大越偏向语义匹配</span>
          </div>
          <div class="param-control">
            <input
              type="range"
              min="0.1" max="0.9" step="0.05"
              v-model.number="currentParams.alpha"
            />
            <span class="param-value">{{ currentParams.alpha.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <div class="params-hint">
        <p>调整后的参数会自动应用到对应案件类型的检索中。</p>
        <p>如不确定如何设置，点击"恢复默认值"使用推荐配置。</p>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

const STORAGE_KEY = 'legal_search_params'

const DEFAULTS = {
  "民商事诉讼案件": { dense_top_k: 18, sparse_top_k: 18, alpha: 0.55 },
  "刑事辩护案件": { dense_top_k: 22, sparse_top_k: 18, alpha: 0.35 },
  "行政诉讼案件": { dense_top_k: 18, sparse_top_k: 18, alpha: 0.40 },
}

const tabs = [
  { key: "民商事诉讼案件", label: "民商事诉讼" },
  { key: "刑事辩护案件", label: "刑事辩护" },
  { key: "行政诉讼案件", label: "行政诉讼" },
]

export default {
  name: 'ParamsPage',
  setup() {
    const activeTab = ref(tabs[0].key)
    const params = ref({})

    function makeDefault() {
      const o = {}
      for (const [k, v] of Object.entries(DEFAULTS)) {
        o[k] = { ...v }
      }
      return o
    }

    const currentParams = computed(() => {
      return params.value[activeTab.value] || DEFAULTS[activeTab.value]
    })

    function loadParams() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
          const saved = JSON.parse(raw)
          const merged = makeDefault()
          for (const key of Object.keys(DEFAULTS)) {
            if (saved[key]) {
              if (saved[key].dense_top_k != null) merged[key].dense_top_k = saved[key].dense_top_k
              if (saved[key].sparse_top_k != null) merged[key].sparse_top_k = saved[key].sparse_top_k
              if (saved[key].alpha != null) merged[key].alpha = saved[key].alpha
            }
          }
          params.value = merged
        } else {
          params.value = makeDefault()
        }
      } catch {
        params.value = makeDefault()
      }
    }

    function saveParams() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(params.value))
    }

    function resetDefaults() {
      params.value = makeDefault()
      saveParams()
    }

    onMounted(loadParams)
    onMounted(() => {
      const stop = setInterval(saveParams, 500)
      window.addEventListener('beforeunload', saveParams)
      return () => clearInterval(stop)
    })

    return { params, activeTab, currentParams, tabs, resetDefaults }
  },
}
</script>

<style scoped>
.params-layout {
  display: flex;
  flex-direction: column;
}

.params-main {
  display: flex;
  flex-direction: column;
}

.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: -1px;
}

.tab-btn {
  padding: 10px 20px;
  border: 1px solid #e5e7eb;
  background: #fafafa;
  font-size: 14px;
  cursor: pointer;
  color: #666;
  border-radius: 8px 8px 0 0;
  margin-right: -1px;
  position: relative;
  z-index: 1;
}

.tab-btn.active {
  background: #fff;
  color: #2563eb;
  font-weight: 600;
  border-bottom-color: #fff;
  z-index: 2;
}

.params-card {
  background: #fff;
  border-radius: 0 10px 10px 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  gap: 24px;
}

.param-row:last-child {
  border-bottom: none;
}

.param-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.param-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.param-desc {
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.param-control {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.param-control input[type="range"] {
  width: 160px;
  accent-color: #2563eb;
}

.param-value {
  display: inline-block;
  width: 48px;
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border-radius: 6px;
  padding: 4px 0;
}

.params-hint {
  margin-top: 20px;
  padding: 14px 18px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  font-size: 13px;
  color: #92400e;
  line-height: 1.7;
}
</style>
