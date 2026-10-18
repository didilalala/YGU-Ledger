/** 服务商预设：选择服务商后自动带出推荐的模型名，Base URL 留空则用后端内置的官方地址 */
export const PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek', model: 'deepseek-chat', vision: false },
  { value: 'qwen', label: '通义千问', model: 'qwen-plus', vision: false },
  { value: 'openai', label: 'OpenAI', model: 'gpt-4o', vision: true },
  { value: 'claude', label: 'Claude', model: 'claude-sonnet-5-5', vision: true },
]

export const providerName = (value) => PROVIDERS.find((p) => p.value === value)?.label || value
