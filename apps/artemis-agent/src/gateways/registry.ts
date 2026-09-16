export interface GatewayAdapter {
  id: string
  send(payload: unknown): Promise<void>
}

export const gatewayRegistry: string[] = [
  'telegram',
  'discord',
  'slack',
  'whatsapp',
  'signal',
  'matrix',
  'mattermost',
  'email',
  'sms',
  'imessage',
  'dingtalk',
  'feishu',
  'wecom',
  'wechat',
  'webhooks',
  'home-assistant'
]
