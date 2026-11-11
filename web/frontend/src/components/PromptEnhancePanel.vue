<template>
  <div class="prompt-enhance-panel">
    <n-space vertical size="large">
      <!-- CTF/渗透模式（Tab 布局） -->
      <n-card :title="$t('enhance.ctfMode')" size="small">
        <n-tabs type="line" animated>



          <!-- ── Claude Code ── -->
          <n-tab-pane name="claude_code" display-directive="show">
            <template #tab>
              <span class="tab-label">
                <span class="status-dot" :class="{ 'dot-success': ctfStore.status?.claude_installed }"></span>
                Claude Code
              </span>
            </template>

            <n-space vertical size="large" style="padding-top: 4px">
              <!-- 提示词模板（最上面：先选模板再看启用） -->
              <div class="mode-section">
                <div class="mode-header">
                  <n-text strong>{{ $t('enhance.editPromptShared') }}</n-text>
                </div>
                <n-text depth="3" style="font-size: 13px; line-height: 1.6">{{ $t('enhance.ctfTemplateDesc') }}</n-text>
                <n-spin :show="ctfStore.prompts.claude_code.loading" style="margin-top: 8px">
                  <div class="template-row">
                    <n-select v-model:value="claudeSelectedTemplate" size="small" :placeholder="ctfStore.templates.claude_code.length === 0 ? $t('enhance.noTemplates') : $t('enhance.selectTemplate')" :options="templateOptions('claude_code')" :disabled="ctfStore.templates.claude_code.length === 0" :render-label="(option) => renderTemplateLabel(option, 'claude_code')" clearable style="flex: 1" @update:value="(v) => { if (v) applyTemplate('claude_code', v) }" />
                    <n-button size="small" :disabled="ctfStore.templates.claude_code.length >= MAX_TEMPLATES" @click="openSaveTemplate('claude_code')">+ {{ $t('enhance.saveAsTemplate') }}</n-button>
                  </div>
                  <n-input :aria-label="$t('enhance.editPromptShared')" v-model:value="claudePromptText" type="textarea" :rows="8" style="font-family: monospace; font-size: 12px" />
                  <n-space style="margin-top: 8px" align="center">
                    <n-button size="small" :disabled="ctfStore.prompts.claude_code.is_default" @click="handleResetPrompt('claude_code')">{{ $t('enhance.restoreDefault') }}</n-button>
                    <n-button size="small" type="primary" @click="handleSavePrompt('claude_code', claudePromptText)">{{ $t('common.save') }}</n-button>
                  </n-space>
                </n-spin>
              </div>

              <n-divider style="margin: 4px 0" />

              <!-- CTF/渗透模式启用 -->
              <div class="mode-section">
                <div class="mode-header">
                  <n-text strong>{{ $t('enhance.ctfMode') }}</n-text>
                  <n-tag :type="ctfStore.status?.claude_installed ? 'success' : 'default'" size="small" :bordered="false">
                    {{ ctfStore.status?.claude_installed ? $t('common.enabled') : $t('common.disabled') }}
                  </n-tag>
                  <n-tag type="info" size="small" :bordered="false">{{ $t('claude.globalScope') }}</n-tag>
                </div>
                <n-text depth="3" style="font-size: 13px; line-height: 1.6">{{ $t('enhance.claudeDesc') }}</n-text>
                <p class="command-inline-hint">{{ $t('claude.globalPrompt') }}：<code>{{ ctfStore.status?.claude_global_prompt_path }}</code></p>
                <n-alert type="info" :bordered="false" style="margin-top: 4px">{{ $t('enhance.claudeWarning') }}</n-alert>
                <div style="margin-top: 8px">
                  <n-button v-if="!ctfStore.status?.claude_installed" type="primary" size="small" :loading="ctfStore.claudeInstallLoading" @click="handleClaudeInstall">{{ $t('enhance.enable') }}</n-button>
                  <n-button v-else type="warning" size="small" :loading="ctfStore.claudeInstallLoading" @click="handleClaudeUninstall">{{ $t('enhance.disable') }}</n-button>
                </div>
                <p v-if="ctfStore.status?.claude_installed" class="command-inline-hint">
                  {{ $t('enhance.activationCommand') }}：<button class="copy-command" type="button" :title="$t('common.copy')" @click="copyCommand('claude')"><code>claude</code></button>
                </p>
              </div>
            </n-space>
          </n-tab-pane>



        </n-tabs>
      </n-card>

      <!-- 提示词改写器（仅 CTF 启用时显示） -->
      <n-card v-if="anyCtfEnabled" :title="$t('enhance.promptRewrite')" size="small">
        <n-space vertical>
          <n-text depth="3" style="font-size: 13px; line-height: 1.6">{{ $t('enhance.promptRewriteDesc') }}</n-text>

          <n-form-item :label="$t('enhance.originalPrompt')">
            <n-input
              v-model:value="rewriteInput" type="textarea" :rows="3"
              :placeholder="$t('enhance.originalPromptPlaceholder')"
            />
          </n-form-item>

          <n-space align="center">
            <n-button
              type="primary"
              :disabled="!rewriteInput.trim() || !settingsStore.aiEnabled || !settingsStore.aiEndpoint || !settingsStore.aiModel"
              :loading="ctfStore.rewriteLoading" @click="handleRewrite"
            >{{ $t('enhance.aiRewriteBtn') }}</n-button>
            <n-alert
              v-if="!settingsStore.aiEnabled || !settingsStore.aiEndpoint || !settingsStore.aiModel"
              type="warning" :bordered="false" style="padding: 4px 10px"
            >{{ $t('enhance.noAiConfig') }}</n-alert>
          </n-space>

          <div id="rewrite-result">
            <n-card v-if="ctfStore.rewrittenRequest" size="small" style="margin-top: 4px">
              <template #header>
                <n-space align="center">
                  <span>{{ $t('enhance.rewrittenPrompt') }}</span>
                  <n-tag size="small" type="info">{{ ctfStore.rewriteStrategy }}</n-tag>
                </n-space>
              </template>
              <n-input :value="ctfStore.rewrittenRequest" type="textarea" :rows="4" readonly />
              <template #action>
                <n-space>
                  <n-button size="small" type="primary" @click="copyRewritten">{{ $t('enhance.copyResult') }}</n-button>
                  <n-button size="small" @click="clearRewrite">{{ $t('common.clear') }}</n-button>
                </n-space>
              </template>
            </n-card>
          </div>

          <n-alert v-if="ctfStore.rewriteError" type="error" :bordered="false">
            {{ ctfStore.rewriteError }}
          </n-alert>
        </n-space>
      </n-card>

      <!-- 推荐工作流 -->
      <n-card :title="$t('help.workflow')" size="small">
        <n-tabs type="segment" size="small">

          <n-tab-pane name="claude" tab="Claude Code">
            <n-steps vertical :current="0" size="small" style="margin-top: 12px">
              <n-step :title="$t('help.workflowCtfSteps[0]')" :description="$t('enhance.claudeDesc')" />
              <n-step :title="$t('help.workflowCtfSteps[1]')" description="claude" />
              <n-step :title="$t('help.workflowCtfSteps[2]')" :description="$t('enhance.promptRewriteDesc')" />
              <n-step :title="$t('help.workflowCtfSteps[3]')" :description="$t('help.workflowCtfSteps[4]')" />
            </n-steps>
          </n-tab-pane>

        </n-tabs>
      </n-card>
    </n-space>

    <!-- 保存模板对话框 -->
    <n-modal
      v-model:show="saveTemplateModal.show"
      preset="dialog"
      :title="$t('enhance.saveAsTemplate')"
      :positive-text="$t('common.confirm')"
      :negative-text="$t('common.cancel')"
      @positive-click="confirmSaveTemplate"
    >
      <n-input
        v-model:value="saveTemplateModal.name"
        :placeholder="$t('enhance.templateNameHint')"
        :maxlength="20"
        show-count
        @keydown.enter="confirmSaveTemplate"
        style="margin-top: 8px"
      />
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage, useDialog, NButton } from 'naive-ui'
import { useCTFStore } from '../stores/ctfStore'
import { useSettingsStore } from '../stores/settingsStore'

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()
const ctfStore = useCTFStore()
const settingsStore = useSettingsStore()

// 任意 CTF 模式已启用时才显示改写功能
const anyCtfEnabled = computed(() => Boolean(ctfStore.status?.claude_installed))

const MAX_TEMPLATES = 5

const rewriteInput = ref('')
const claudePromptText = ref('')
const claudeSelectedTemplate = ref(null)
// 保存模板对话框状态
const saveTemplateModal = ref({ show: false, tool: '', name: '' })

onMounted(async () => {
  await Promise.all([
    ctfStore.fetchStatus(),
    ctfStore.fetchPrompt('claude_code'),
    ctfStore.fetchTemplates('claude_code'),
  ])
  claudePromptText.value = ctfStore.prompts.claude_code.prompt
  // 用 is_default 判断是否匹配默认模板，选中对应模板名
  for (const tool of ['claude_code']) {
    if (ctfStore.prompts[tool].is_default) {
      const defaultTpl = ctfStore.templates[tool].find(t => t.default === true)
      if (defaultTpl) getSelectedTemplateRef(tool).value = defaultTpl.name
    }
  }
})

// ─── 模板相关 ──────────────────────────────────────────

function templateOptions(tool) {
  return ctfStore.templates[tool].map(tpl => ({
    label: tpl.name,
    value: tpl.name,
    builtin: tpl.builtin || false,
  }))
}

function renderTemplateLabel(option, tool) {
  const isBuiltin = option.builtin === true
  const children = [
    h('span', {
      style: 'flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap',
    }, option.label),
  ]
  if (!isBuiltin) {
    children.push(h(NButton, {
      text: true,
      size: 'tiny',
      type: 'error',
      focusable: false,
      style: 'flex-shrink:0; padding: 0 4px',
      onClick: (e) => {
        e.stopPropagation()
        confirmDeleteTemplate(tool, option.value)
      },
    }, { default: () => '✕' }))
  }
  return h('div', {
    style: 'display:flex; align-items:center; justify-content:space-between; width:100%; gap:8px',
  }, children)
}

async function applyTemplate(tool, templateName) {
  getSelectedTemplateRef(tool).value = templateName
  const prompt = await ctfStore.fetchTemplatePrompt(tool, templateName)
  if (prompt) {
    getPromptTextRef(tool).value = prompt
  }
}

function openSaveTemplate(tool) {
  const text = getPromptTextRef(tool).value
  if (!text?.trim()) {
    message.warning(t('enhance.promptEmpty'))
    return
  }
  saveTemplateModal.value = { show: true, tool, name: '' }
}

async function confirmSaveTemplate() {
  const name = saveTemplateModal.value.name.trim()
  if (!name) return false  // 阻止对话框关闭
  const tool = saveTemplateModal.value.tool
  const prompt = getPromptTextRef(tool).value
  const result = await ctfStore.saveTemplate(tool, name, prompt)
  if (result.success) {
    message.success(t('enhance.templateSaved'))
    saveTemplateModal.value.show = false
  } else {
    message.error(result.message)
    return false
  }
}

function confirmDeleteTemplate(tool, name) {
  dialog.warning({
    title: t('common.confirm'),
    content: `删除模板「${name}」？`,
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      const result = await ctfStore.deleteTemplate(tool, name)
      if (result.success) {
        message.success(t('enhance.templateDeleted'))
      } else {
        message.error(result.message)
      }
    },
  })
}

// ─── 提示词管理 ──────────────────────────────────────────

function getPromptTextRef() {
  return claudePromptText
}

function getSelectedTemplateRef() {
  return claudeSelectedTemplate
}

async function handleSavePrompt(tool, text) {
  const result = await ctfStore.savePrompt(tool, text)
  if (result.success) {
    message.success(t('enhance.promptSaved'))
  } else {
    message.error(result.message || t('enhance.promptSaveError'))
  }
}

async function handleResetPrompt(tool) {
  const result = await ctfStore.resetPromptToDefault(tool)
  if (result.success) {
    getPromptTextRef(tool).value = ctfStore.prompts[tool].prompt
    message.success(t('enhance.promptRestored'))
  }
}

// ─── CTF 安装/卸载 ──────────────────────────────────────





async function handleClaudeInstall() {
  const result = await ctfStore.installClaude()
  message[result.success ? 'success' : 'error'](result.message)
}

async function handleClaudeUninstall() {
  dialog.warning({
    title: t('common.confirm'),
    content: t('enhance.confirmDisableClaude'),
    positiveText: t('common.confirm'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      const result = await ctfStore.uninstallClaude()
      message[result.success ? 'success' : 'error'](result.message)
    }
  })
}



// ─── 提示词改写 ──────────────────────────────────────────

async function handleRewrite() {
  if (!rewriteInput.value.trim()) return
  const result = await ctfStore.rewritePrompt(rewriteInput.value)
  if (result.success) {
    message.success(t('enhance.rewriteSuccess'))
    nextTick(() => {
      document.getElementById('rewrite-result')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    })
  }
}

async function writeClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()

  try {
    if (!document.execCommand('copy')) throw new Error('copy failed')
  } finally {
    document.body.removeChild(textarea)
  }
}

async function copyCommand(command) {
  try {
    await writeClipboard(command)
    message.success(t('common.copied'))
  } catch {
    message.error(t('common.error'))
  }
}

async function copyRewritten() {
  await copyCommand(ctfStore.rewrittenRequest)
}

function clearRewrite() {
  rewriteInput.value = ''
  ctfStore.resetRewrite()
}
</script>

<style scoped>
.prompt-enhance-panel {
  max-width: 800px;
  margin: 0 auto;
}

code {
  background: rgba(128, 128, 128, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
}

.mode-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.command-inline-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--n-text-color-3);
  line-height: 1.6;
}

.copy-command {
  border: 0;
  background: transparent;
  padding: 0;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.copy-command code {
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.copy-command:hover code,
.copy-command:focus-visible code {
  background: rgba(99, 226, 183, 0.18);
  box-shadow: 0 0 0 1px rgba(99, 226, 183, 0.45);
}

.copy-command:focus-visible {
  outline: none;
}

.app-launch-hint {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.injection-mode-radio {
  margin-top: 4px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--n-text-color-disabled, #ccc);
}

.status-dot.dot-success {
  background: #18a058;
}

.status-dot.dot-warning {
  background: #f0a020;
}
</style>
