const moment = require('moment')
require('moment/locale/zh-cn')
moment.locale('zh-cn')

class TimeManager {
  constructor() {
    this.lastInteractionTime = new Map()
  }

  // 获取当前时间信息
  getCurrentTimeInfo() {
    const now = moment()

    return {
      time: now.format('HH:mm'),
      date: now.format('YYYY-MM-DD'),
      weekday: now.format('dddd'),
      hour: now.hour(),
      period: this.getTimePeriod(now.hour()),
      greeting: this.getTimeGreeting(now.hour())
    }
  }

  // 获取时间段
  getTimePeriod(hour) {
    if (hour >= 5 && hour < 8) return '清晨'
    if (hour >= 8 && hour < 11) return '上午'
    if (hour >= 11 && hour < 13) return '中午'
    if (hour >= 13 && hour < 17) return '下午'
    if (hour >= 17 && hour < 19) return '傍晚'
    if (hour >= 19 && hour < 22) return '晚上'
    return '深夜'
  }

  // 获取时间问候语
  getTimeGreeting(hour) {
    if (hour >= 5 && hour < 11) return '早上好'
    if (hour >= 11 && hour < 13) return '中午好'
    if (hour >= 13 && hour < 18) return '下午好'
    if (hour >= 18 && hour < 22) return '晚上好'
    return '夜深了'
  }

  // 记录互动时间
  recordInteraction(userId) {
    this.lastInteractionTime.set(userId, moment())
  }

  // 获取距离上次互动的时间
  getTimeSinceLastInteraction(userId) {
    const lastTime = this.lastInteractionTime.get(userId)
    if (!lastTime) return null

    const now = moment()
    const duration = moment.duration(now.diff(lastTime))

    const hours = Math.floor(duration.asHours())
    const minutes = Math.floor(duration.asMinutes()) % 60

    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return { days, hours: hours % 24, minutes, text: `${days}天${hours % 24}小时` }
    } else if (hours > 0) {
      return { hours, minutes, text: `${hours}小时${minutes}分钟` }
    } else if (minutes > 0) {
      return { minutes, text: `${minutes}分钟` }
    } else {
      return { seconds: Math.floor(duration.asSeconds()), text: '刚刚' }
    }
  }

  // 生成时间感知的上下文
  generateTimeContext(userId) {
    const timeInfo = this.getCurrentTimeInfo()
    const timeSince = this.getTimeSinceLastInteraction(userId)

    let context = `当前时间：${timeInfo.date} ${timeInfo.weekday} ${timeInfo.time}（${timeInfo.period}）\n`

    if (timeSince) {
      if (timeSince.days > 0) {
        context += `距离上次聊天：${timeSince.text}（好久没见了）\n`
      } else if (timeSince.hours > 3) {
        context += `距离上次聊天：${timeSince.text}（有一段时间了）\n`
      } else if (timeSince.hours > 0) {
        context += `距离上次聊天：${timeSince.text}\n`
      }
    } else {
      context += `这是第一次聊天\n`
    }

    return context
  }

  // 判断是否应该主动问候
  shouldGreet(userId) {
    const timeSince = this.getTimeSinceLastInteraction(userId)

    if (!timeSince) return true  // 第一次聊天
    if (timeSince.days > 0) return true  // 超过一天
    if (timeSince.hours >= 6) return true  // 超过6小时

    return false
  }

  // 生成问候语
  generateGreeting(userId) {
    const timeInfo = this.getCurrentTimeInfo()
    const timeSince = this.getTimeSinceLastInteraction(userId)

    if (!timeSince) {
      return `${timeInfo.greeting}，哥哥...第一次见面...请多关照...的说`
    }

    if (timeSince.days > 0) {
      return `哥哥！好久不见...独角兽和优酱都很想你...的说（已经${timeSince.text}了）`
    }

    if (timeSince.hours >= 6) {
      return `${timeInfo.greeting}，哥哥...终于回来了...的说`
    }

    return null  // 不需要特殊问候
  }
}

module.exports = new TimeManager()
