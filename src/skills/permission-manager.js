// 权限等级
const PERMISSION_LEVELS = {
  GUEST: 0,      // 访客
  USER: 1,       // 普通用户
  VIP: 2,        // VIP用户
  ADMIN: 3,      // 管理员
  OWNER: 4       // 所有者
}

// 技能定义
const SKILLS = {
  // 基础技能（所有人可用）
  basic: {
    level: PERMISSION_LEVELS.GUEST,
    commands: {
      '/help': {
        description: '显示帮助',
        handler: 'showHelp'
      },
      '/clear': {
        description: '清除对话历史',
        handler: 'clearHistory'
      },
      '/service': {
        description: '查看当前AI服务',
        handler: 'showService'
      }
    }
  },

  // 用户技能
  user: {
    level: PERMISSION_LEVELS.USER,
    commands: {
      '/stats': {
        description: '查看个人统计',
        handler: 'showStats'
      },
      '/mood': {
        description: '查看当前心情',
        handler: 'showMood'
      },
      '/memory': {
        description: '查看记忆',
        handler: 'showMemory'
      }
    }
  },

  // VIP技能
  vip: {
    level: PERMISSION_LEVELS.VIP,
    commands: {
      '/switch': {
        description: '切换AI模型',
        handler: 'switchModel'
      },
      '/voice': {
        description: '切换语音模式',
        handler: 'toggleVoice'
      }
    }
  },

  // 管理员技能
  admin: {
    level: PERMISSION_LEVELS.ADMIN,
    commands: {
      '/adduser': {
        description: '添加用户到白名单',
        handler: 'addUser'
      },
      '/removeuser': {
        description: '移除用户',
        handler: 'removeUser'
      },
      '/whitelist': {
        description: '查看白名单',
        handler: 'showWhitelist'
      },
      '/broadcast': {
        description: '广播消息',
        handler: 'broadcast'
      }
    }
  },

  // 所有者技能
  owner: {
    level: PERMISSION_LEVELS.OWNER,
    commands: {
      '/reset': {
        description: '重置所有数据',
        handler: 'resetAll'
      },
      '/export': {
        description: '导出数据',
        handler: 'exportData'
      },
      '/setperm': {
        description: '设置用户权限',
        handler: 'setPermission'
      }
    }
  }
}

class PermissionManager {
  constructor() {
    this.userPermissions = new Map()
    this.defaultPermission = PERMISSION_LEVELS.USER
  }

  // 设置用户权限
  setUserPermission(userId, level) {
    this.userPermissions.set(userId, level)
  }

  // 获取用户权限
  getUserPermission(userId) {
    return this.userPermissions.get(userId) || this.defaultPermission
  }

  // 检查用户是否有权限执行命令
  hasPermission(userId, command) {
    const userLevel = this.getUserPermission(userId)

    for (const [category, skillSet] of Object.entries(SKILLS)) {
      if (skillSet.commands[command]) {
        return userLevel >= skillSet.level
      }
    }

    return false
  }

  // 获取用户可用的命令列表
  getAvailableCommands(userId) {
    const userLevel = this.getUserPermission(userId)
    const commands = []

    for (const [category, skillSet] of Object.entries(SKILLS)) {
      if (userLevel >= skillSet.level) {
        for (const [cmd, info] of Object.entries(skillSet.commands)) {
          commands.push({
            command: cmd,
            description: info.description,
            category: category
          })
        }
      }
    }

    return commands
  }

  // 获取权限等级名称
  getPermissionName(level) {
    const names = {
      [PERMISSION_LEVELS.GUEST]: '访客',
      [PERMISSION_LEVELS.USER]: '用户',
      [PERMISSION_LEVELS.VIP]: 'VIP',
      [PERMISSION_LEVELS.ADMIN]: '管理员',
      [PERMISSION_LEVELS.OWNER]: '所有者'
    }
    return names[level] || '未知'
  }
}

module.exports = {
  PermissionManager,
  PERMISSION_LEVELS,
  SKILLS
}
