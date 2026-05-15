<template>
  <div class="chat-layout">
    <section class="chat-main">
      <div class="section-header">
        <h2>智能问答</h2>
      </div>

      <div class="chat-messages" ref="msgBox">
        <div v-if="messages.length === 0" class="chat-empty">
          输入问题开始对话
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          :class="['chat-bubble', msg.role === 'user' ? 'user' : 'assistant']"
        >
          <div class="bubble-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div class="bubble-text">{{ msg.content }}</div>
        </div>
        <div v-if="thinking" class="chat-bubble assistant">
          <div class="bubble-label">AI</div>
          <div class="bubble-text thinking">思考中...</div>
        </div>
      </div>

      <div class="chat-input-box">
        <textarea
          v-model="input"
          placeholder="输入你的问题..."
          rows="2"
          :disabled="thinking"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="btn btn-primary" :disabled="!canSend" @click="send">
          发送
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, nextTick, computed } from 'vue'
import { sendLegalChat } from '../api/entries.js'

function generateSessionId() {
  return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

export default {
  name: 'ChatPage',
  setup() {
    const messages = ref([])
    const input = ref('')
    const thinking = ref(false)
    const sessionId = ref(generateSessionId())
    const msgBox = ref(null)

    const canSend = computed(() => input.value.trim() && !thinking.value)

    function scrollBottom() {
      nextTick(() => {
        const el = msgBox.value
        if (el) el.scrollTop = el.scrollHeight
      })
    }

    async function send() {
      const text = input.value.trim()
      if (!text || thinking.value) return

      messages.value.push({ role: 'user', content: text })
      input.value = ''
      thinking.value = true
      scrollBottom()

      let paramOverrides = {}
      try {
        const raw = localStorage.getItem('legal_search_params')
        if (raw) {
          paramOverrides = JSON.parse(raw)
        }
      } catch {}

      try {
        const res = await sendLegalChat(text, sessionId.value, paramOverrides)
        messages.value.push({ role: 'assistant', content: res.answer })
      } catch (e) {
        messages.value.push({ role: 'assistant', content: '抱歉，出错了: ' + e.message })
      } finally {
        thinking.value = false
        scrollBottom()
      }
    }

    return {
      messages, input, thinking, sessionId, msgBox,
      canSend, send,
    }
  },
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
}

.chat-main {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-empty {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 48px 0;
}

.chat-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-bubble.user {
  align-self: flex-end;
  background: #2563eb;
  color: #fff;
}

.chat-bubble.user .bubble-label {
  color: rgba(255,255,255,0.7);
}

.chat-bubble.assistant {
  align-self: flex-start;
  background: #fff;
  border: 1px solid #e5e7eb;
  white-space: pre-wrap;
}

.chat-bubble.assistant .bubble-label {
  color: #999;
}

.bubble-label {
  font-size: 11px;
  margin-bottom: 4px;
  font-weight: 600;
}

.thinking {
  color: #999;
  font-style: italic;
}

.chat-input-box {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-top: 1px solid #e5e7eb;
}

.chat-input-box textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  transition: border-color 0.15s;
}

.chat-input-box textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
</style>
