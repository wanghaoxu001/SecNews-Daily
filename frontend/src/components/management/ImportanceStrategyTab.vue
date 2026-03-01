<template>
  <div>
    <n-alert type="info" style="margin-bottom: 16px;">
      当前使用策略：<strong>样本对比策略（Strategy A）</strong> — 根据同分类典型样本，利用 LLM 判断新闻重要性。
    </n-alert>
    <n-radio-group v-model:value="strategy">
      <n-space vertical>
        <n-radio value="sample_based">样本对比策略（推荐）— 使用分类典型样本 + LLM 判定</n-radio>
        <n-radio value="rule_based" disabled>规则策略（开发中）— 基于关键词和正则规则</n-radio>
      </n-space>
    </n-radio-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NAlert, NRadioGroup, NRadio, NSpace } from 'naive-ui'

const strategy = ref('sample_based')
</script>
