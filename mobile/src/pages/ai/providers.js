/** 服务商预设：选择服务商后自动带出推荐的模型名，Base URL 留空则用后端内置的官方地址 */
export const PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek', model: 'deepseek-chat', vision: false, logo: '/static/provider-deepseek.png' },
  { value: 'qwen', label: '通义千问', model: 'qwen-plus', vision: false, logo: '/static/provider-qwen.png' },
  { value: 'openai', label: 'OpenAI', model: 'gpt-4o', vision: true, logo: '/static/provider-openai.png' },
  { value: 'claude', label: 'Claude', model: 'claude-sonnet-5-5', vision: true, logo: '/static/provider-claude.png' },
]

export const providerName = (value) => PROVIDERS.find((p) => p.value === value)?.label || value

export const providerLogo = (value) => PROVIDERS.find((p) => p.value === value)?.logo || ''
