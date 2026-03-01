<template>
  <AppLayout>
    <section class="page-container page-container--wide">
      <h2 class="page-title management-title">系统管理</h2>
      <n-tabs type="line" v-model:value="activeTab" animated>
        <n-tab-pane name="news" tab="新闻管理">
          <NewsManagementTab />
        </n-tab-pane>
        <n-tab-pane name="llm" tab="LLM 配置">
          <LlmConfigTab />
        </n-tab-pane>
        <n-tab-pane name="rss" tab="RSS 源管理">
          <RssSourcesTab />
        </n-tab-pane>
        <n-tab-pane name="task" tab="定时任务">
          <TaskConfigTab />
        </n-tab-pane>
        <n-tab-pane name="processing" tab="处理参数">
          <ProcessingConfigTab />
        </n-tab-pane>
        <n-tab-pane name="examples" tab="重要性样本">
          <ImportanceExamplesTab />
        </n-tab-pane>
        <n-tab-pane name="strategy" tab="重要性策略">
          <ImportanceStrategyTab />
        </n-tab-pane>
      </n-tabs>
    </section>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NTabs, NTabPane } from 'naive-ui'
import AppLayout from '../components/layout/AppLayout.vue'
import NewsManagementTab from '../components/management/NewsManagementTab.vue'
import LlmConfigTab from '../components/management/LlmConfigTab.vue'
import RssSourcesTab from '../components/management/RssSourcesTab.vue'
import TaskConfigTab from '../components/management/TaskConfigTab.vue'
import ProcessingConfigTab from '../components/management/ProcessingConfigTab.vue'
import ImportanceExamplesTab from '../components/management/ImportanceExamplesTab.vue'
import ImportanceStrategyTab from '../components/management/ImportanceStrategyTab.vue'

const activeTab = ref('news')
</script>

<style scoped>
.management-title {
  margin-bottom: var(--space-4);
}
</style>
