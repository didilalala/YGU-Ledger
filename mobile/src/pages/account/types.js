/** 账户类型，value 与后端 Account.TYPE_CHOICES 一致 */
export const ACCOUNT_TYPES = [
  { value: 'bank_card', label: '银行卡', icon: '💳' },
  { value: 'e_wallet', label: '电子钱包', icon: '📱' },
  { value: 'credit_card', label: '信用卡', icon: '🏦' },
  { value: 'cash', label: '现金', icon: '💵' },
]

export const accountType = (value) => ACCOUNT_TYPES.find((t) => t.value === value) || ACCOUNT_TYPES[0]
