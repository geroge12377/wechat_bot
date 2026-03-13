const db = require('./database')
const moment = require('moment')

class EmotionManager {
  constructor() {
    this.emotions = {
      '普通': { intensity: 5, description: '日常状态' },
      '开心': { intensity: 8, description: '心情很好' },
      '兴奋': { intensity: 9, description: '非常激动' },
      '害羞': { intensity: 6, description: '有点不好意思' },
      '低落': { intensity: 3, description: '有点难过' },
      '吃醋': { intensity: 4, description: '有点不开心' },
      '温和': { intensity: 7, description: '温柔的状态' }
    }
  }

  async init() {
    await db.init()
  }

  // 分析用户消息，判断应该触发的情感
  analyzeEmotion(message, currentAffection = 50) {
    const positiveWords = ['喜欢', '爱', '可爱', '漂亮', '好', '棒', '厉害', '开心', '高兴']
    const negativeWords = ['讨厌', '烦', '走开', '不要', '滚']
    const intimateWords = ['抱抱', '亲亲', '摸头', '陪我', '想你']
    const jealousWords = ['其他', '别人', '她', '女孩']

    let emotion = '普通'
    let intensity = 5

    // 检查吃醋
    if (jealousWords.some(word => message.includes(word))) {
      emotion = '吃醋'
      intensity = 6
    }
    // 检查亲密
    else if (intimateWords.some(word => message.includes(word))) {
      emotion = '害羞'
      intensity = 7
    }
    // 检查积极
    else if (positiveWords.some(word => message.includes(word))) {
      emotion = currentAffection >= 70 ? '兴奋' : '开心'
      intensity = 8
    }
    // 检查消极
    else if (negativeWords.some(word => message.includes(word))) {
      emotion = '低落'
      intensity = 3
    }
    // 根据好感度决定默认情感
    else {
      if (currentAffection >= 80) {
        emotion = '开心'
        intensity = 7
      } else if (currentAffection >= 60) {
        emotion = '温和'
        intensity = 6
      } else {
        emotion = '普通'
        intensity = 5
      }
    }

    return { emotion, intensity }
  }

  // 计算好感度和亲密度变化
  calculateRelationshipChange(message) {
    let affectionChange = 0
    let intimacyChange = 0

    const positiveWords = ['喜欢', '爱', '可爱', '漂亮', '好', '棒', '厉害']
    const negativeWords = ['讨厌', '烦', '走开', '不要']
    const intimateWords = ['抱抱', '亲亲', '摸头', '陪我', '想你', '爱你']

    // 积极词汇增加好感度
    positiveWords.forEach(word => {
      if (message.includes(word)) affectionChange += 2
    })

    // 消极词汇减少好感度
    negativeWords.forEach(word => {
      if (message.includes(word)) affectionChange -= 3
    })

    // 亲密词汇增加亲密度和好感度
    intimateWords.forEach(word => {
      if (message.includes(word)) {
        intimacyChange += 3
        affectionChange += 1
      }
    })

    // 普通对话也会小幅增加
    if (affectionChange === 0 && intimacyChange === 0) {
      affectionChange = 1
      intimacyChange = 1
    }

    return { affectionChange, intimacyChange }
  }

  // 获取情感描述
  getEmotionDescription(emotion) {
    return this.emotions[emotion]?.description || '未知状态'
  }

  // 获取情感强度
  getEmotionIntensity(emotion) {
    return this.emotions[emotion]?.intensity || 5
  }
}

module.exports = new EmotionManager()
