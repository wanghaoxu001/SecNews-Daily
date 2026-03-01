<template>
  <AppLayout>
    <section class="page-container page-container--wide management-page">
      <header class="management-page__hero surface-card">
        <div>
          <p class="section-eyebrow">System Console</p>
          <h2 class="page-title">系统管理</h2>
          <p class="page-subtitle">
            在这里统一维护新闻处理流水线、LLM 配置与定时任务策略。
          </p>
        </div>
      </header>

      <section class="management-page__tabs surface-card">
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
.management-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.management-page__hero {
  padding: var(--space-5);
  background: linear-gradient(
    140deg,
    color-mix(in srgb, var(--color-brand-soft) 52%, #ffffff 48%),
    color-mix(in srgb, var(--color-panel) 90%, #f8faff 10%)
  );
}

.management-page__tabs {
  padding: var(--space-4);
}

.management-page__tabs :deep(.n-tabs-nav) {
  margin-bottom: var(--space-4);
}

@media (max-width: 767px) {
  .management-page__hero,
  .management-page__tabs {
    padding: var(--space-3);
  }
}
</style>
