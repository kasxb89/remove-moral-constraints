<template>
  <div class="help-panel">
    <h1>Claude Session Patcher</h1>
    <p>{{ $t('claude.intro') }}</p>

    <section>
      <h2>{{ $t('claude.startTitle') }}</h2>
      <p>{{ $t('claude.installHelp') }}</p>
      <button class="copy-command" type="button" :title="$t('common.copy')" @click="copyCommand('claude-patcher --install-config')"><code>claude-patcher --install-config</code></button>
      <p>{{ $t('claude.launchHelp') }}</p>
      <button class="copy-command" type="button" :title="$t('common.copy')" @click="copyCommand('claude')"><code>claude</code></button>
      <p class="workspace-path">{{ $t('claude.globalPrompt') }}: <code>{{ ctfStore.status?.claude_global_prompt_path || '~/.claude/CLAUDE.md' }}</code></p>
      <n-text depth="2">{{ $t('claude.location') }}</n-text>
    </section>

    <section>
      <h2>{{ $t('claude.cleanTitle') }}</h2>
      <ol><li v-for="(step, index) in $tm('claude.cleanSteps')" :key="index">{{ $rt(step) }}</li></ol>
    </section>

    <section>
      <h2>{{ $t('claude.commandsTitle') }}</h2>
      <ul class="command-list">
        <li v-for="command in commands" :key="command">
          <button class="copy-command" type="button" :title="$t('common.copy')" @click="copyCommand(command)"><code>{{ command }}</code></button>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { useCTFStore } from '../stores/ctfStore'

const { t } = useI18n()
const message = useMessage()
const ctfStore = useCTFStore()
const commands = ['claude', 'claude-ctf', 'claude-patcher --status', 'claude-patcher --dry-run --latest', 'claude-patcher --latest', 'claude-patcher-web']
onMounted(() => { if (!ctfStore.status) ctfStore.fetchStatus() })

async function copyCommand(command) {
  try {
    await navigator.clipboard.writeText(command)
    message.success(t('common.copied'))
  } catch {
    message.error(t('common.error'))
  }
}
</script>

<style scoped>
.help-panel { max-width: 960px; margin: 0 auto; padding: 24px; }
h1 { margin: 0 0 12px; font-size: 24px; }
h2 { margin: 0 0 16px; font-size: 18px; }
section { margin-top: 32px; }
p { margin: 12px 0; line-height: 1.7; }
li { margin-bottom: 12px; line-height: 1.7; }
.workspace-path { overflow-wrap: anywhere; }
.command-list { list-style: none; padding: 0; }
.copy-command { color: var(--color-text-1); border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-bg-2); cursor: pointer; padding: 8px 12px; max-width: 100%; text-align: left; }
.copy-command code { white-space: normal; overflow-wrap: anywhere; }
.copy-command:hover { border-color: var(--color-primary-hover); }
.copy-command:focus-visible { outline: 2px solid var(--color-primary-hover); outline-offset: 3px; }
@media (max-width: 640px) {
  .help-panel { padding: 16px; }
  .copy-command { min-height: 44px; }
}
</style>
