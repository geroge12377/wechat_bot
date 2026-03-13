// 白名单配置
module.exports = {
  // 是否启用白名单
  enabled: false,  // 改为关键词模式，不限制用户

  // 白名单用户列表（微信ID或昵称）
  users: [
    '五谷杂粮',           // 昵称
    // 'wxid_xxx',        // 微信ID
    // '添加更多用户...'
  ],

  // 白名单群聊列表
  rooms: [
    // '测试群',
    // '添加群聊名称...'
  ],

  // 黑名单（优先级高于白名单）
  blacklist: [
    // '不想回复的用户'
  ],

  // 是否回复群消息
  replyInRoom: true,

  // 是否需要@才回复（仅群聊）
  requireMention: false,

  // 关键词触发模式
  keywordMode: {
    enabled: true,  // 启用关键词模式
    keywords: [
      '独角兽',
      '妹妹',
      '@独角兽'
    ],
    // 是否需要完全匹配（false = 包含即可）
    exactMatch: false
  }
}
